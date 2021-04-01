#include <iostream>

#include "zendar-api.h"
#include "reqrep.pb.h"

int main(int argc, char* argv[]) {
  if (argc < 2) {
    printf("Usage: example-control URI");
  }
  zendar::ZendarReceiver rcv(argv[1]);
  zendar::ZendarError error;
  zen_proto::control::Response rep;
  rcv.Connect();
  // Reset the ZPU
  rcv.Stop();
  rcv.Status(rep);
  if (rep.status().state() == zen_proto::control::RepStatus::READY) {
    std::cout << "ZPU ready" << "\n";
  } else {
    std::cout << "ZPU not ready" << "\n";
  }
  rcv.ListConfigurations(rep);
  if (!rep.has_list_configurations()) {
    std::cout << "Failed to list configurations";
  }
  std::cout << "Available configurations:" << "\n";
  for (auto config : rep.list_configurations().configurations()) {
    std::cout << config << "\n";
  }
  // For this example, run the first configuration in the list
  std::string first_config(*rep.list_configurations().configurations().begin());
  rcv.Start(first_config);
  if (rep.status().state() == zen_proto::control::RepStatus::RUNNING) {
    std::cout << "Successfully started";
  } else {
    std::cout << "Failed to start";
  }
  rcv.Stop();
  return 1;
}
