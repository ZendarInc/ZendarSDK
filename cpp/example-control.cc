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
  rcv.Stop();
  rcv.Status(rep);
  if (rep.status().state() == zen_proto::control::RepStatus::READY) {
    std::cout << "ZPU ready" << "\n";
  } else {
    std::cout << "ZPU not ready" << "\n";
    return 0;
  }
  rcv.ListConfigurations(rep);
  if (!rep.has_list_configurations()) {
    std::cout << "Failed to list configurations";
    return 0;
  }
  std::cout << "Available configurations:" << "\n";
  for (auto config : rep.list_configurations().configurations()) {
    std::cout << config << "\n";
  }
  return 1;
}
