#include <zendar/client/api/api.h>

#include <gflags/gflags.h>
#include <glog/logging.h>

#include <iostream>
#include <fstream>
#include <vector>
#include <thread>
#include <chrono>
#include <atomic>

using namespace std::literals;


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
  vehicle_name, "",
  "The vehicle name for vehicle.pt"
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

DEFINE_double(
  kill_temp, 75.0,
  "Temperature threshold for the device, in deg-C."
  "Sends a stop if the CPU or GPU temperature exceeds this value."
);

using namespace zen::api;

std::atomic<bool> early_terminate;


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
SpinPoints(int* total_pc_counter, int* total_pc_frame_counter)
{
  while (auto next_points = ZenApi::NextTrackerState()) {
    *total_pc_counter += next_points->detection_size();
    *total_pc_frame_counter += 1;
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
    VLOG(1) << report->DebugString();

    if (report->report_case() == zpb::telem::HousekeepingReport::kHeartbeat) {
      *is_running = report->heartbeat().is_running();
    }

    if (report->report_case() == zpb::telem::HousekeepingReport::kTemperatures) {
      const auto& temperatures = report->temperatures();
      auto cpu_temp = temperatures.cpu_temperature();
      auto gpu_temp = temperatures.gpu_temperature();

      if (cpu_temp >= FLAGS_kill_temp || gpu_temp >= FLAGS_kill_temp) {
        LOG(ERROR)
          << "FATAL Device temperatue exceeded the kill threshold. HALTING! "
          << "{ kill_temp: " << FLAGS_kill_temp
          << ", CPU_temp: " << cpu_temp
          << ", GPU_temp: " << gpu_temp << " }.";
        ZenApi::Stop();
        early_terminate = true;
      }
    }
  }
}

} ///< \namespace


int
main(int argc, char* argv[])
{
  ZenApi::Init();
  google::ParseCommandLineFlags(&argc, &argv, false);

  bool is_running = true;
  int total_pc_counter = 0;
  int total_pc_frame_counter = 0;
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
  ZenApi::Start(FLAGS_imaging_mode, FLAGS_vehicle_name, 
                default_install_options, FLAGS_stream_addr);

  std::cout << "radar started" << std::endl;
  log_file << "Running Mode: " << FLAGS_imaging_mode << std::endl;

  // subscribe to radar data
  ZenApi::SubscribeImages();
  ZenApi::SubscribeTrackerStates();
  ZenApi::SubscribeLogMessages();
  ZenApi::SubscribeHousekeepingReports();

  // listen to data
  auto image_reader = std::thread(SpinImages, &image_counter);
  auto points_reader = std::thread(SpinPoints, &total_pc_counter, &total_pc_frame_counter);
  auto log_reader = std::thread(SpinLogs, &log_file);
  auto hk_reader = std::thread(SpinHK, &is_running);

  auto start = std::chrono::steady_clock::now();
  auto end = start + std::chrono::seconds(FLAGS_run_duration);
  while (std::chrono::steady_clock::now() < end && !early_terminate) {
    std::this_thread::sleep_for(50ms);
  }

  // before closing down, log data
  log_file << "total points received: " << total_pc_counter << std::endl;
  log_file << "total point clouds received: " << total_pc_frame_counter << std::endl;
  log_file << "total sar images received: " << image_counter << std::endl;

  if (is_running) {
    log_file << "clean exit" << std::endl;
  }
  else {
    log_file << "failed exit" << std::endl;
  }
  log_file.close();

  // stop radar processor
  ZenApi::UnsubscribeImages();
  ZenApi::UnsubscribeTrackerStates();

  ZenApi::Release();
  image_reader.join();
  points_reader.join();
  ZenApi::Stop();

  // keep logging a few moments longer to flush the queue
  std::this_thread::sleep_for(500ms);

  // disconnect from the log channels
  ZenApi::UnsubscribeHousekeepingReports();
  ZenApi::UnsubscribeLogMessages();

  ZenApi::Disconnect();
  hk_reader.join();
  log_reader.join();

  if (is_running) {
    return EXIT_SUCCESS;
  }
  else {
    return EXIT_FAILURE;
  }
}
