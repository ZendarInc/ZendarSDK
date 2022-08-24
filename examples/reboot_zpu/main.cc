#include <zendar/api/api.h>

#include <glog/logging.h>
#include <gflags/gflags.h>

#include <thread>
#include <chrono>

#include <iostream>

DEFINE_string(
  device_addr, "localhost",
  "IPv4 address of the device to connect to. This can be a resolvable hostname "
  "or given in dotted notation."
);

using namespace zen::api;


int
main(int argc, char* argv[])
{ 
  ZenApi::Init(&argc, &argv);

  auto default_telem_ports = ZenApi::TelemPortOptions();
  ZenApi::Connect(FLAGS_device_addr, default_telem_ports);

  // Get shannon_imaging running status from Heartbeat
  ZenApi::SubscribeHousekeepingReports();
  auto hk_report = ZenApi::NextHousekeepingReport();

  if (hk_report->has_heartbeat()) {
    const auto& heartbeat = hk_report->heartbeat();
    if (heartbeat.is_running()) {
      // stop shannon imaging before reboot the ZPU
      ZenApi::Stop();
    }
  }

  ZenApi::RebootZPU();
  ZenApi::Disconnect();

  // 90 seconds may be not enough for the reboot and connect
  std::this_thread::sleep_for(std::chrono::seconds(90));

  ZenApi::Connect(FLAGS_device_addr, default_telem_ports);
  ZenApi::Disconnect();

  return EXIT_SUCCESS;
}
