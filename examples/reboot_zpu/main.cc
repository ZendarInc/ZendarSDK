#include <zendar/api/api.h>

#include <glog/logging.h>
#include <gflags/gflags.h>

#include <thread>
#include <chrono>

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
  ZenApi::RebootZPU();
  ZenApi::Disconnect();

  // 90 seconds may be not enough for the reboot and connect
  std::this_thread::sleep_for(std::chrono::seconds(90));

  ZenApi::Connect(FLAGS_device_addr, default_telem_ports);
  ZenApi::Disconnect();

  return EXIT_SUCCESS;
}
