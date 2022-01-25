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

} ///< \namespace


int
main(int argc, char* argv[])
{
  ZenApi::Init(&argc, &argv);

  auto default_data_ports = ZenApi::DataPortOptions();
  ZenApi::Bind(default_data_ports);

  ZenApi::SubscribeImages();
  ZenApi::SubscribeTrackerStates();
  ZenApi::SubscribeTracklogs();

  auto image_reader = std::thread(SpinImages);
  auto points_reader = std::thread(SpinPoints);
  auto tracklogs_reader = std::thread(SpinTracklogs);

  std::this_thread::sleep_for(120s);

  ZenApi::UnsubscribeImages();
  ZenApi::UnsubscribeTrackerStates();
  ZenApi::UnsubscribeTracklogs();

  ZenApi::Release();

  image_reader.join();
  points_reader.join();
  tracklogs_reader.join();

  return EXIT_SUCCESS;
}
