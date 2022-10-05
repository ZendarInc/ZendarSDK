#include <zendar/client/api/api.h>

#include <gflags/gflags.h>

#include <thread>

DEFINE_string(
  device_addr, "localhost",
  "IPv4 address of the device to connect to. This can be a resolvable hostname "
  "or given in dotted notation."
);

DEFINE_string(
  imaging_mode, "choose-a-mode",
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

using namespace zen::api;


int
main(int argc, char* argv[])
{
  ZenApi::Init();
  google::ParseCommandLineFlags(&argc, &argv, false);

  auto default_telem_ports = ZenApi::TelemPortOptions();
  ZenApi::Connect(FLAGS_device_addr, default_telem_ports);

  auto default_install_options = ZenApi::InstallOptions();
  ZenApi::Start(FLAGS_imaging_mode, FLAGS_vehicle_name, 
                default_install_options, FLAGS_stream_addr);

  ZenApi::Disconnect();

  return EXIT_SUCCESS;
}
