#include <zendar/api/api.h>

#include <glog/logging.h>
#include <gflags/gflags.h>

#include <thread>

DEFINE_string(
  device_addr, "localhost",
  "IPv4 address of the device to connect to. This can be a resolvable hostname "
  "or given in dotted notation."
);

using namespace zen::api;
using namespace std::literals;


namespace {

void
SpinImages()
{
  while (auto next_image = ZenApi::NextImage()) {
    (void)next_image;
    LOG(INFO) << "SUCCESS Got an Image!";
  }
}

void
SpinPoints()
{
  while (auto next_points = ZenApi::NextTrackerState()) {
    (void)next_points;
    LOG(INFO) << "SUCCESS Got a Tracker State!";
  }
}

void
SpinTracklogs()
{
  while (auto next_tracklog = ZenApi::NextTracklog()) {
    (void)next_tracklog;
    LOG(INFO) << "SUCCESS Got a Tracklog!";
  }
}

void
SpinHK()
{
  while (auto next_hk = ZenApi::NextHousekeepingReport()) {
    LOG(INFO) << "SUCCESS Got a Housekeeping Report!";
    VLOG(1) << next_hk->DebugString();
  }
}

void
SpinLogs()
{
  while (auto next_log = ZenApi::NextLogMessage()) {
    (void)next_log;
    LOG(INFO) << "SUCCESS Got a Log Message!";
  }
}


} ///< \namespace


int
main(int argc, char* argv[])
{
  ZenApi::Init(&argc, &argv);

  auto default_telem_ports = ZenApi::TelemPortOptions();
  ZenApi::Connect(FLAGS_device_addr, default_telem_ports);

  auto default_data_ports = ZenApi::DataPortOptions();
  ZenApi::Bind(default_data_ports);

  ZenApi::SubscribeImages();
  ZenApi::SubscribeTrackerStates();
  ZenApi::SubscribeTracklogs();
  ZenApi::SubscribeHousekeepingReports();
  ZenApi::SubscribeLogMessages();

  auto image_reader = std::thread(SpinImages);
  auto points_reader = std::thread(SpinPoints);
  auto tracklogs_reader = std::thread(SpinTracklogs);
  auto hk_reader = std::thread(SpinHK);
  auto log_reader = std::thread(SpinLogs);

  std::this_thread::sleep_for(120s);

  ZenApi::UnsubscribeImages();
  ZenApi::UnsubscribeTrackerStates();
  ZenApi::UnsubscribeTracklogs();
  ZenApi::UnsubscribeHousekeepingReports();
  ZenApi::UnsubscribeLogMessages();

  ZenApi::Release();
  ZenApi::Disconnect();

  image_reader.join();
  points_reader.join();
  tracklogs_reader.join();
  hk_reader.join();
  log_reader.join();

  return EXIT_SUCCESS;
}
