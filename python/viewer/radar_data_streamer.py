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


class ProtoStreamReader(object):
    """
    This class streams data stored in protobuf binary stream and
    returns python object type
    """
    def __init__(self, data_stream_path, proto_type, python_type,
                 header_size=8):
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
        self.data_stream = None

    def __enter__(self):
        self.data_stream = open(self.data_stream_path, 'rb')
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


class ProtoStreamWriter(object):
    """
    This class writes protobuf objects to file stream
    """
    def __init__(self, output_file_path, header_size=8):
        self.output_file_path = output_file_path
        self.header_size = header_size
        self.write_stream = None

    def __enter__(self):
        self.write_stream = open(self.output_file_path, 'wb')

        # add dummy header
        header = b"\x00" * self.header_size
        self.write_stream.write(header)
        return self

    def write(self, record):
        serial = record.SerializeToString()
        length = len(serial)

        self.write_stream.write(pack('<I', length))
        self.write_stream.write(serial)

    def __exit__(self, exc_type, exc_value, traceback):
        self.write_stream.close()


class MultiRadarStreamReader(object):
    """
    Takes in multiple radar streams and return aligned radar data

    TODO:: this function now only handles two radars
    """
    def __init__(self, radar_data_readers):
        assert isinstance(radar_data_readers, list), \
                "radar_data_readers is not a list"

        assert len(radar_data_readers) == 2, \
                "MultiRadarStreamReader currently only supports two radars"

        self.radar_data_readers = []
        for reader in radar_data_readers:
            self.radar_data_readers.append(iter(reader))

    def __iter__(self):
        return self

    def __next__(self):
        """
        return the next frame-id aligned radar data
        """
        radar_data_0 = next(self.radar_data_readers[0])
        radar_data_1 = next(self.radar_data_readers[1])
        frame_id_0 = radar_data_0.frame_id
        frame_id_1 = radar_data_1.frame_id

        # we continue to iterate between all the radar streams
        # until we find a match
        while frame_id_0 != frame_id_1:
            if frame_id_0 < frame_id_1:
                radar_data_0 = next(self.radar_data_reader_0)
                frame_id_0 = radar_data_0.frame_id
            else:
                radar_data_1 = next(self.radar_data_reader_1)
                frame_id_1 = radar_data_1.frame_id

        return (radar_data_0, radar_data_1)


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
