
# Zendar SDK


## Introduction:

This document describes the usage of the Zendar API library, which is the interface to the ZPU device. The ZPU outputs several protobuf data streams, namely: SAR images, a point cloud of radar detections, its current position, and log messages. This API allows you to access each of those streams independently using the `ZendarReceiver `class.


## Requirements:


```
libgoogle-glog0v5
libnng
libprotobuf
protobuf-compiler
g++
```



## Setup (Ubuntu):

Install the requirements:


```
sudo apt install libgoogle-glog0v5 libgoogle-glog-dev libprotobuf-dev protobuf-compiler g++ git cmake
```


Then clone and install the nng library:


```
git clone https://github.com/nanomsg/nng.git
cd nng
git checkout b74e76c  # i.e Revision 1.2.4
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PATH=/usr/local \
        -DNNG_TESTS:BOOL=OFF \
        -DNNG_TOOLS:BOOL=OFF \
        -DNNG_ENABLE_TLS:BOOL=OFF \
        -DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON
make -j
sudo make install
sudo ldconfig
```


Install the library using `make`:


```
cd ZendarSDK/cpp
sudo make all
```



## Types:

Included in `zendar-api.h:`

	Main interface:


```
ZendarReceiver
```


Error codes:


```
ZendarError
```


Included in `data.pb.h`


    Data types (protobufs):


```
    zen_proto::data::Image
    zen::tracker::message::TrackerState
    zen_proto::data::Position
    zen_proto::data::LogRecord
```



## Methods of `ZendarReceiver`:


```
ZendarReceiver(std::string URI)
```


The constructor takes a URI as a parameter. This should be the TCP subscribe port of the ZPU, which will default to port 6342. For example, for a ZPU with IP address` 10.0.0.1`, the URI will be` tcp://10.0.0.1:6342`


```
ZendarError SubscribeImages(std::size_t queue_size);
ZendarError SubscribeTracker(std::size_t queue_size);
ZendarError SubscribeTracklog(std::size_t queue_size);
ZendarError SubscribeLogs(std::size_t queue_size);
```


The Subscribe functions connect to the ZPU output of their respective data types. Each takes an optional parameter setting the length of the receive queue. If the receive queue fills up, new data will be dropped. If the subscription was successful, these functions will return `ZENDAR_API_OK, `otherwise they will return `ZENDAR_SUBSCRIBE_FAILURE.`


```
ZendarError UnsubscribeImages();
ZendarError UnsubscribeTracker();
ZendarError UnsubscribeTracklog();
ZendarError UnsubscribeLogs();
```


The Unsubscribe functions clean up the socket and queues from a previous Subscribe. Note that unsubscribing from a data stream will clear the receive queue, so reading data is only possible during an active subscription. If the unsubscribe is successful, these will return `ZENDAR_API_OK, `otherwise they will return `ZENDAR_UNSUBSCRIBE_FAILURE, `including if the unsubscribe failed due to not being subscribed. Unsubscribing may cause a `Receive timed out `warning to be written to the console, this is expected behavior.


```
ZendarError NextImage(shannon::data::Image& proto, int timeout = -1);
ZendarError NextTracker(zen::tracker::message::TrackerState& proto,
                Int timeout = -1);
ZendarError NextTracklog(shannon::data::Position& proto, int = -1);
ZendarError NextLogMessage(shannon::data::LogRecord& proto, int = -1);
```


The Next functions read the oldest data in their respective receive queues into the protobuf object passed in as a parameter. If the queue is empty, they will wait for `timeout `milliseconds for more data to show up, and if none does, they will return `ZENDAR_API_QUEUE_ERROR. `Negative values for `timeout `will wait forever.` `Otherwise, they will return `ZENDAR_API_OK `for a successful read or another error code depending on the failure (see error codes 3-7 below).

Note that even with a long timeout on this call, if there is a long pause in data, the network thread will time out, and produce both a warning message and put an error in the queue, which will be reported here. This is likely to happen if no log messages are produced for a while, or if the receiver is subscribed to a data stream that is not being produced, for example subscribing to the tracker output if the ZPU is running in SAR-only mode.


## Error codes:


```
ZENDAR_API_OK = 0
```


The operation was successful.


```
ZENDAR_API_SUBSCRIBE_FAILURE = 1
```


Failed to subscribe to the data stream.


```
ZENDAR_API_UNSUBSCRIBE_FAILURE = 2
```


Failed to unsubscribe to the data stream.


```
ZENDAR_API_TIMEOUT = 3
```


Timeout error in receiving data from the socket.


```
ZENDAR_API_QUEUE_ERROR = 4
```


Failed to read the next data element due to a failure to pop from the receive queue, usually due to a timeout on an empty queue.


```
ZENDAR_API_NOT_SUBSCRIBED = 5,
```


Failed to read the next data element because the receiver is not subscribed to that data stream.


```
ZENDAR_API_PROTOBUF_ERROR = 6,
```


Failed to unmarshal the protobuf received from the ZPU. Check to make sure the versions of the ZPU firmware and the API are compatible. 


```
ZENDAR_API_OTHER_ERROR = 7
```


Catchall for other errors that may occur.



Example usage:


```
#include <zendar-api.h>
#include <data.pb.h>

ZendarReceiver rcv("tcp://10.0.0.1:6342");
zen_proto::data::Image;
rcv.SubscribeImages(100);
// Receive images while some condition is true
while (condition) {
  ZendarError error = rcv.NextImage(image);
  if (error) {
    /* Handle error */
  }
  /* Process data*/
}
rcv.UnsubscribeImages();
