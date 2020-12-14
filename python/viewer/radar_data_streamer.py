from struct import pack, unpack

from abc import ABC, abstractmethod


class RadarData(ABC):
    """
    Abstract radar data type stored in pbs stream
    """
    @classmethod
    @abstractmethod
    def from_proto(cls, data_pb):
        pass


class RadarDataStreamer(object):
    """
    This class streams data stored in protobuf binary stream and
    returns python object type
    """
    def __init__(self, data_stream_path, proto_type, python_type,
                 header_size=8, mode='rb'):
        """
        data_stream_path  -- radar data protobuf stream file path
        proto_type        -- protobuf type
        python_type       -- Python class to be converted to
        header_size       -- size of the header in the binary stream
        """
        self.data_stream_path = data_stream_path
        self.proto_type = proto_type
        self.python_type = python_type
        self.header_size = header_size
        self.mode = mode
        self.data_stream = None

    def __enter__(self):
        self.data_stream = open(self.data_stream_path, self.mode)
        if self.mode == 'wb':
            # write 8 bytes header
            self.data_stream.write(b"\x41\x48\x41\x56\x00\x00\x00\x00")
        return self

    def __iter__(self):
        """
        initialize the iterator

        move file pointer pass the header
        """
        if self.header_size > 0:
            _ = self.data_stream.read(self.header_size)
        return self

    def __next__(self):
        data_pb = read_protobuf_message(self.data_stream, self.proto_type)
        if data_pb is None:
            raise StopIteration

        python_obj = self.python_type.from_proto(data_pb)
        return python_obj

    def __exit__(self, exc_type, exc_value, traceback):
        self.data_stream.close()

    def append(self, record):
        assert isinstance(record, self.proto_type)

        serial = record.SerializeToString()
        length = len(serial)

        self.data_stream.write(pack('<I', length))
        self.data_stream.write(serial)


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
