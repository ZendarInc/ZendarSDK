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

  ZenApi::SubscribeHousekeepingReports();
  ZenApi::SubscribeLogMessages();

  auto hk_reader = std::thread(SpinHK);
  auto log_reader = std::thread(SpinLogs);

  std::this_thread::sleep_for(120s);

  ZenApi::UnsubscribeHousekeepingReports();
  ZenApi::UnsubscribeLogMessages();

  ZenApi::Disconnect();

  hk_reader.join();
  log_reader.join();

  return EXIT_SUCCESS;
}
