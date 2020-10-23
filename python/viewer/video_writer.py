from subprocess import (
    Popen,
    PIPE,
    CalledProcessError,
    check_output,
)


class VideoWriter(object):

    """
    Video encoder and writer.
    """

    def __init__(self, output_file, w, h, frames_per_second,
                 rate_factor=0, keyframe_interval=5):
        assert w > 0
        assert h > 0
        self.output_file = output_file
        self.fps = frames_per_second
        self.w = w
        self.h = h
        self.rate_factor = rate_factor
        self.keyframe_interval = keyframe_interval

        # Check if this is an nvidia accelerated ffmpeg, or not.
        if self.is_nvidia_accelerated():
            self.ffmpeg_cmd = ['ffmpeg', '-y',
                               '-loglevel', 'warning',
                               '-f', 'rawvideo',
                               '-vcodec', 'rawvideo',
                               '-s', '%dx%d' % (self.w, self.h),
                               '-pix_fmt', 'rgb24',
                               '-r', '%d' % self.fps,
                               '-i', '-',
                               '-an',
                               '-vcodec', 'h264_nvenc',
                               '-pix_fmt', 'yuv444p',
                               '-cq', '0',
                               '-g', '%d' % self.keyframe_interval,
                               self.output_file]
        else:
            self.ffmpeg_cmd = ['ffmpeg', '-y',
                               '-loglevel', 'warning',
                               '-f', 'rawvideo',
                               '-vcodec', 'rawvideo',
                               '-s', '%dx%d' % (self.w, self.h),
                               '-pix_fmt', 'rgb24',
                               '-r', '%f' % self.fps,
                               '-i', '-',
                               '-an',
                               '-vcodec', 'libx264',
                               '-pix_fmt', 'yuv444p',
                               '-crf', '%d' % self.rate_factor,
                               '-g', '%d' % self.keyframe_interval,
                               self.output_file]

    def is_nvidia_accelerated(self):
        return b'enable-nvenc' in check_output(['ffmpeg', '-version'])

    def __enter__(self):
        self.proc = Popen(self.ffmpeg_cmd, stdin=PIPE)
        return self

    def __call__(self, data):
        """
        Encode and output one video frame.
        """
        self.proc.stdin.write(data.tostring())
        return data

    def __exit__(self, exc_type, exc_value, traceback):
        self.proc.stdin.close()
        code = self.proc.wait()
        self.proc = None
        if code:
            raise CalledProcessError(code, self.ffmpeg_cmd)
