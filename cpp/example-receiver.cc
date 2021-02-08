#include "zendar-api.h"
#include "data.pb.h"

int main(int argc, char* argv[]) {
  if (argc < 2) {
    printf("Usage: example-receiver URI");
  }
  zendar::ZendarReceiver rcv(argv[1]);
  rcv.SubscribeImages(100);
  rcv.SubscribeTracker(100);
  rcv.SubscribeTracklog(100);
  rcv.SubscribeLogs(100);

  printf("Successful Initialization\n");
  zen_proto::data::Image image;
  zen::tracker::message::TrackerState tracker_state;
  zen_proto::data::Position position;
  zen_proto::data::LogRecord log;

  zendar::ZendarError error;
  for (int i=0; i<10; ++i) {
    error = rcv.NextImage(image);
    if (error) {
      printf("Failed to receive image\n");
    } else {
      printf("Received image, timestamp: %f \n", image.timestamp());
    }
    error = rcv.NextTracker(tracker_state);
    if (error) {
      printf("Failed to receive tracker_state\n");
    } else {
      printf("Received image, timestamp: %f \n",
             tracker_state.timestamp().common());
    }
    error = rcv.NextTracklog(position);
    if (error) {
      printf("Failed to receive position\n");
    } else {
      printf("Received position:\n %f\n %f\n %f \n",
             position.position().x(),
             position.position().y(),
             position.position().z());
    }
    error = rcv.NextLogMessage(log);
    if (error) {
      printf("Failed to receive log\n");
    } else {
      printf("Received log: %s\n", log.message().c_str());
    }
  }
  rcv.UnsubscribeImages();
  rcv.UnsubscribeTracker();
  rcv.UnsubscribeTracklog();
  rcv.UnsubscribeLogs();
  return 1;
}
