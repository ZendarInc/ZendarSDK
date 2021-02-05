#include <chrono>
#include <thread>

#include "zendar-api.h"
#include "data.pb.h"

int main() {
  zendar::ZendarReceiver rcv("tcp://127.0.0.1:6342");
  rcv.SubscribeImages(10);
  printf("Success\n");
  zen_proto::data::Image image;
  for (int i=0; i<10; ++i) {
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));    
    rcv.NextImage(image);
  }
  rcv.UnsubscribeImages();
  return 1;
}
