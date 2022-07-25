#include <zendar/api/api.h>

#include <glog/logging.h>
#include <gflags/gflags.h>



#include <google/protobuf/text_format.h>

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
    (void)next_hk;

    if (next_hk->has_heartbeat()) {
      const auto& heartbeat = next_hk->heartbeat();
      LOG(INFO)
        << "Got Heartbeat messages" << "\n"
        << "Heartbeat: " << heartbeat.echo() << "\n";
    }
    if (next_hk->has_sensor_identity()) {
      const auto& sensor_identity = next_hk->sensor_identity();
      LOG(INFO) 
        << "Got Sensor Identity messages" << "\n"
        << "Serial: " << sensor_identity.serial() << "\n"
        << "System Major: " << sensor_identity.system_major() << "\n"
        << "System Minor: " << sensor_identity.system_minor() << "\n"
        << "Channel: " << sensor_identity.channel() << "\n"
        << "Radar Extrinsic R w: " << sensor_identity.extrinsic().r().w() << "\n"
        << "Radar Extrinsic R x: " << sensor_identity.extrinsic().r().x() << "\n"
        << "Radar Extrinsic R y: " << sensor_identity.extrinsic().r().y() << "\n"
        << "Radar Extrinsic R z: " << sensor_identity.extrinsic().r().z() << "\n"
        << "Radar Extrinsic T x: " << sensor_identity.extrinsic().t().x() << "\n"
        << "Radar Extrinsic T y: " << sensor_identity.extrinsic().t().y() << "\n"
        << "Radar Extrinsic T Z: " << sensor_identity.extrinsic().t().z() << "\n"
        << "Radar Extrinsic Time: " << sensor_identity.extrinsic().time() << "\n";
    }

    if (next_hk->has_imaging_status()) {
      const auto& imaging_status = next_hk->imaging_status();

      std::string is_running = "false";
      if (imaging_status.is_running() != 0) is_running = "true";
 
      LOG(INFO) 
        << "Got Imaging Status messages" << "\n"
        << "Imaging is running: " << is_running << "\n"
        << "Running Mode: " << imaging_status.running_mode()<< "\n";
    }
    
    if (next_hk->has_gps_status()) {
      const auto& gps_status = next_hk->gps_status();
      LOG(INFO) 
        << "Got GPS Status messages" << "\n"
        << "Satellite Count: " << gps_status.qos().satellite_count() << "\n"
        << "GPS Status: " << gps_status.qos().gps_status() << "\n"
        << "Ins Status: " << gps_status.qos().ins_status() << "\n";
    }
    
    if (next_hk->has_temperatures()) {
      const auto& temperatures  = next_hk->temperatures();
      LOG(INFO) 
        << "Got Temperatures messages" << "\n"
        << "CPU Temperatures: " << temperatures.cpu_temperature() << " Celsius" << "\n"
        << "GPU Temperatures: " << temperatures.gpu_temperature() << " Celsius" << "\n";
    }
    if (next_hk->has_memory_usage()) {
      const auto& memory_usage = next_hk->memory_usage();
      LOG(INFO) 
        << "Got Memory Usage messages" << "\n"
        << "CPU/GPU Memory Usage: " << memory_usage.cpu_memory_usage() / 1'000'000 << "MB" << "\n"
        << "CPU/GPU Memory Total: " << memory_usage.cpu_total_memory() / 1'000'000 << "MB" << "\n";
    }
    if (next_hk->has_utilization()) {
      const auto& utilization = next_hk->utilization();
      LOG(INFO) 
        << "Got utilization messages" << "\n"
        << "CPU Utilization: " << utilization.cpu_utilization() << "%" << "\n"
        << "GPU Utilization: " << utilization.gpu_utilization() << "%" << "\n";
    }
  }
}

void
SpinLogs()
{
  while (auto next_log = ZenApi::NextLogMessage()) {
    (void)next_log;
    VLOG(1) << "SUCCESS Got a Log Message!";
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
