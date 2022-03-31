#include <zendar/api/api.h>

#include <gflags/gflags.h>

#include <iostream>
#include <fstream>
#include <vector>
#include <thread>
#include <chrono>


DEFINE_string(
  device_addr, "localhost",
  "IPv4 address of the device to connect to. This can be a resolvable hostname "
  "or given in dotted notation."
);

DEFINE_string(
  install_path, "/usr/bin",
  "Where the Zendar binaries are installed."
);

DEFINE_string(
  imaging_mode, "",
  "The imaging mode to be run."
);

DEFINE_string(
  stream_addr, "localhost",
  "Where the device should stream the image data. "
  "**Note** This flag tells the device where to send the image data, so this "
  "address should be from the device's viewpoint."
);

DEFINE_int32(
  run_duration, 120,
  "How long (in seconds) to run this program before disconnect. "
);

DEFINE_string(
  log_path, "log.txt",
  "file path of the output log file."
);

using namespace zen::api;


namespace {

bool
ModeExists(ZenApi::Mode mode, std::vector<ZenApi::Mode> modes)
{
  if (std::find(modes.begin(), modes.end(), mode) != modes.end()){
    return true;
  }
  else {
    return false;
  }
}

void
SpinImages(int* image_counter)
{
  while (auto next_image = ZenApi::NextImage()) {
    (void)next_image;
    *image_counter += 1;
  }
}

void
SpinPoints(int* pc_counter)
{
  while (auto next_points = ZenApi::NextTrackerState()) {
    (void)next_points;
    std::cout << "got points " << pc_counter << std::endl;
    *pc_counter += 1;
  }
}

void
SpinLogs(std::ofstream* file)
{
  while (auto next_log = ZenApi::NextLogMessage()) {
    std::cout << next_log->canonical_message() << std::endl;
    if (next_log->severity() >= 0){
      (*file) << next_log->canonical_message() << std::endl;
    }
  }
}

void
SpinHK(bool* is_running)
{
  while (auto report = ZenApi::NextHousekeepingReport()) {
    if (report->report_case() == zpb::telem::HousekeepingReport::kImagingStatus){
      *is_running = report->imaging_status().is_running();
    }
  }
}

} ///< \namespace


int
main(int argc, char* argv[])
{
  ZenApi::Init(&argc, &argv);

  bool is_running = true;
  int pc_counter = 0;
  int image_counter = 0;

  std::ofstream log_file;
  log_file.open(FLAGS_log_path);

  auto default_telem_ports = ZenApi::TelemPortOptions();
  ZenApi::Connect(FLAGS_device_addr, default_telem_ports);

  auto default_data_ports = ZenApi::DataPortOptions();
  ZenApi::Bind(default_data_ports);

  // verify the input mode actually exists on ZPU
  auto modes = ZenApi::ListModes();
  bool mode_exists = ModeExists(FLAGS_imaging_mode, modes);
  if (!mode_exists){
    std::cout << FLAGS_imaging_mode <<
                " does not exist on ZPU. Available modes are: " << std::endl;

    for (const auto& mode : modes) {
      std::cout << mode << std::endl;
    }

    return EXIT_FAILURE;
  }

  // start the radars
  auto default_install_options = ZenApi::InstallOptions();
  default_install_options.install_path = FLAGS_install_path;
  ZenApi::Start(FLAGS_imaging_mode, default_install_options, FLAGS_stream_addr);

  std::cout << "radar started" << std::endl;

  // subscribe to radar data
  ZenApi::SubscribeImages();
  ZenApi::SubscribeTrackerStates();
  ZenApi::SubscribeLogMessages();
  ZenApi::SubscribeHousekeepingReports();

  // listen to data
  auto image_reader = std::thread(SpinImages, &image_counter);
  auto points_reader = std::thread(SpinPoints, &pc_counter);
  auto log_reader = std::thread(SpinLogs, &log_file);
  auto hk_reader = std::thread(SpinHK, &is_running);

  std::this_thread::sleep_for(
      std::chrono::seconds(FLAGS_run_duration));

  // before closing down, log data
  log_file << "total point clouds received: " << pc_counter << std::endl;
  log_file << "total sar images received: " << image_counter << std::endl;

  if (is_running) {
    log_file << "clean exit" << std::endl;
  }
  else {
    log_file << "failed exit" << std::endl;
  }
  log_file.close();

  // close down
  ZenApi::UnsubscribeImages();
  ZenApi::UnsubscribeTrackerStates();
  ZenApi::UnsubscribeHousekeepingReports();
  ZenApi::UnsubscribeLogMessages();

  ZenApi::Release();
  image_reader.join();
  points_reader.join();

  ZenApi::Disconnect();
  hk_reader.join();
  log_reader.join();

  if (is_running){
    return EXIT_SUCCESS;
  }
  else {
    return EXIT_FAILURE;
  }
}
