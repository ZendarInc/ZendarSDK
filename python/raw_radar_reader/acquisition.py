from gzip import open as gzip_open
from os.path import exists, join, normpath, splitext
from struct import pack, unpack
from google.protobuf.text_format import Merge
from acquisition_pb2 import (
        Acquisition,
)
from primitive_pb2 import (
        Extrinsic,
)
from radar_pb2 import (
#        IntrinsicPose,
#        PoseRecord,
        IntrinsicRadar,
        ChirpResponse,
        )


class SensorPath(object):
    def __init__(self, path, type):
        self.root = splitext(path)[0]
        self.type = type
        self.read_cache = None

    @property
    def exists(self):
        return exists(self.path)

    def read(self):
        """ Cache anything read, just in case somebody uses this code in a
        slightly tighter loop.
        """
        if self.read_cache is None:
            self.read_cache = self._read()

        return self.read_cache


class SensorPbTxt(SensorPath):
    @property
    def path(self):
        return '{}.pt'.format(self.root)

    def _read(self):
        if exists(self.path):
            model = read_proto_text(self.path, self.type())
        else:
            path = replace_suffix(self.path, ".pb")
            assert(exists(path)), path

            model = read_proto_binary(path, self.type())

        return model

    def write(self, data):
        assert(False) << "Not supported"


class SensorStream(SensorPath):
    def __init__(self, *args, **kwargs):
        SensorPath.__init__(self, *args, **kwargs)
        self.stream = None
        self.offset = 0

    @property
    def path(self):
        return '{}.pbs'.format(self.root)

    def __iter__(self):
        with self.open_file() as fp:
            if self.offset:
                fp.seek(self.offset)

            while True:
                data = fp.read(4)
                if len(data) != 4:
                    break

                length = unpack('<I', data)[0]
                data = fp.read(length)
                if len(data) != length:
                    print('Truncated data')
                    raise StopIteration()

                model = self.type()
                model.ParseFromString(data)
                yield model

    def open_file(self):
        openers = [
            ('gz', lambda x: gzip_open(x, 'rb')),
        ]

        for (extension, opener) in openers:
            # Try the appended extension
            path = '{}.{}'.format(self.path, extension)
            if exists(path):
                return opener(path)

            # The path may have already included the appropriate extension,
            # so test that
            ext = splitext(self.path)[1]
            if ext[1:] == extension:
                return opener(self.path)
        else:
            return open(self.path, 'rb')

    def open(self, mode):
        if self.stream is None:
            self.stream = open(self.path, mode)

    def append(self, record):
        assert isinstance(record, self.type)
        self.open('wb')

        serial = record.SerializeToString()
        length = len(serial)

        self.stream.write(pack('<I', length))
        self.stream.write(serial)

    def close(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None


class SensorStreamContextManaged(object):
    """
    This class is intended to be used with the context manager
    to properly close out the file when exit
    """
    def __init__(self, sensor_stream):
        self.sensor_stream = sensor_stream

    def __enter__(self):
        return self.sensor_stream

    def __exit__(self, type, value, traceback):
        self.sensor_stream.close()


class SensorPathModel(object):
    def __init__(self, root, extrinsic, intrinsic, serial, stream):
        self.root = root
        self.serial = serial
        self.type_extrinsic = extrinsic
        self.type_intrinsic = intrinsic
        self.type_stream = stream

    @property
    def extrinsic(self):
        return SensorPbTxt(
                type=self.type_extrinsic,
                path=join(self.root, 'extrinsic'))

    @property
    def intrinsic(self):
        return SensorPbTxt(
                type=self.type_intrinsic,
                path=join(self.root, 'intrinsic'))

    @property
    def stream(self):
        return SensorStream(
                type=self.type_stream,
                path=join(self.root, 'stream'))


class AcquisitionStreamModel(object):
    def __init__(self, root):
        self.root = normpath(root)

    @property
    def acquisition(self):
        return SensorPbTxt(
                type=Acquisition,
                path=join(self.root, 'acquisition'))

    @property
    def tracklog(self):
        return self.pose

    @property
    def pose(self):
        if self.acquisition.exists:
            serial = self.acquisition.read().pose.serial
        else:
            serial = ''

        return SensorPathModel(
                extrinsic=Extrinsic,
                intrinsic=IntrinsicPose,
                stream=PoseRecord,
                serial=serial,
                root=join(self.root, 'tracklog'))

    @property
    def radars(self):
        return [r.name for r in self.acquisition.read().radars]

    def radar(self, name):
        serial = ''
        if self.acquisition.exists:
            for a in self.acquisition.read().radars:
                if name == a.name:
                    serial = a.serial
                    break

        return SensorPathModel(
                extrinsic=Extrinsic,
                intrinsic=IntrinsicRadar,
                stream=ChirpResponse,
                serial=serial,
                root=join(self.root, 'radar', name))

    @property
    def radar_modules(self):
        return [r for r in self.acquisition.read().radar_modules]

    def radar_module(self, module):
        radars = [module.controller]
        radars.extend(module.peripheral)

        models = []
        for radar in radars:
            model = SensorPathModel(extrinsic=Extrinsic,
                                    intrinsic=IntrinsicRadar,
                                    stream=ChirpResponse,
                                    serial=radar.serial,
                                    root=join(self.root, 'radar', radar.name))
            models.append(model)

        return models


def read_proto_binary(path, model):
    with open(path, 'rb') as fp:
        model.ParseFromString(fp.read())

    return model


def read_proto_text(path, model):
    with open(path, 'r') as fp:
        Merge(fp.read(), model)

    return model


def replace_suffix(path, suffix):
    return splitext(path)[0] + suffix
