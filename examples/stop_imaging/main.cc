#include <zendar/client/api/api.h>

#include <gflags/gflags.h>

#include <thread>



DEFINE_string(
  device_addr, "localhost",
  "IPv4 address of the device to connect to. This can be a resolvable hostname "
  "or given in dotted notation."
);

using namespace zen::api;


int
main(int argc, char* argv[])
{
  ZenApi::Init();
  google::ParseCommandLineFlags(&argc, &argv, false);

  auto default_telem_ports = ZenApi::TelemPortOptions();
  ZenApi::Connect(FLAGS_device_addr, default_telem_ports);

  ZenApi::Stop();

  ZenApi::Disconnect();

  return EXIT_SUCCESS;
}
