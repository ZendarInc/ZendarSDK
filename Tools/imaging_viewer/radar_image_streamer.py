from struct import unpack

import data_pb2
from radar_image import RadarImage


class RadarImageStreamer(object):
    """
    stream radar image from a single protobuf file
    """
    def __init__(self, radar_stream_path, header_size=8):
        """
        radar_stream_path  -- radar image protobuf stream file path
        header_size        -- size of the header in the binary stream
        """
        self.radar_stream_path = radar_stream_path
        self.radar_streams = None
        self.header_size = header_size

    def __enter__(self):
        self.radar_stream = open(self.radar_stream_path, "rb")
        return self

    def __iter__(self):
        """
        initialize the iterator

        move file pointer pass the header
        """
        if self.header_size > 0:
            _ = self.radar_stream.read(self.header_size)
        return self

    def __next__(self):
        image_pb = read_protobuf_message(self.radar_stream, data_pb2.Image)
        if image_pb is None:
            raise StopIteration

        radar_image = RadarImage.from_proto(image_pb)
        return radar_image

    def __exit__(self, exc_type, exc_value, traceback):
        self.radar_stream.close()


class MultipleRadarImageStreamer(object):
    """
    Takes in multiple radar image streams and return aligned images
    in time.

    TODO:: this function now only handles two radars
    """
    def __init__(self, radar_image_streamers):
        assert isinstance(radar_image_streamers, list), \
                "radar_image_streamers is not a list"
        self.radar_image_streamers = radar_image_streamers
        zip(self.radar_image_streamers[0], self.radar_image_streamers[1])
        self.image_stream_a = self.radar_image_streamers[0]
        self.image_stream_b = self.radar_image_streamers[1]

    def __iter__(self):
        return self

    def __next__(self):
        """
        return the next timestamp aligned images
        """
        radar_image_a = next(self.image_stream_a)
        radar_image_b = next(self.image_stream_b)
        a_frame_id = radar_image_a.frame_id
        b_frame_id = radar_image_b.frame_id
        while a_frame_id != b_frame_id:
            if a_frame_id < b_frame_id:
                radar_image_a = next(self.image_stream_a)
                a_frame_id = radar_image_a.frame_id
            elif a_frame_id > b_frame_id:
                radar_image_b = next(self.image_stream_b)
                b_frame_id = radar_image_b.frame_id

        image_list = [radar_image_a, radar_image_b]
        return image_list


def read_protobuf_message(fp, message_type):
    """
    read a protobuf message with uint32_t framing

    fp              -- binary stream file pointer
    message type    -- protobuf message class
    """

    # read the message size (first 4 bytes)
    data = fp.read(4)
    if len(data) != 4:
        return None

    # convert byte array into integer
    msg_length = unpack('<I', data)[0]

    # read the entire binary data into memory
    data = fp.read(msg_length)
    if len(data) != msg_length:
        print('Truncated data')
        return None

    # convert to protobuf object
    msg = message_type()
    msg.ParseFromString(data)
    return msg
