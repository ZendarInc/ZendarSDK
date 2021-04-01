#include "zendar-api.h"
#include "data.pb.h"

int main() {
  zendar::ZendarReceiver rcv("tcp://127.0.0.1");
  rcv.SubscribeImages(100);
  printf("Successful Initialization\n");
  zen_proto::data::Image image;
  zendar::ZendarError error;
  for (int i=0; i<10; ++i) {
    error = rcv.NextImage(image);
    if (error) {
      printf("Failed to receive\n");
    } else {
      printf("Received image\n");
    }
  }
  rcv.UnsubscribeImages();
  return 1;
}
