"""Bounded original-frame reuse for overlapping Dance source checks."""
from collections import OrderedDict
import time
import cv2


class SourceFrameReader:
    def __init__(self, source, fps, *, max_bytes=96 * 1024 * 1024):
        self.cap = cv2.VideoCapture(str(source))
        self.cache = OrderedDict()
        self.max_bytes = max_bytes
        self.retained_bytes = 0
        self.stats = dict(reads=0, seeks=0, grabs=0, cache_hits=0, decode_seconds=0.)
        if not self.cap.isOpened() or abs(float(self.cap.get(cv2.CAP_PROP_FPS)) - fps) > .001:
            self.close()
            raise ValueError('source_fps_mismatch')

    def get(self, frame):
        if frame < 0 or int(frame) != frame:
            raise ValueError('source_frame_unavailable')
        frame = int(frame)
        if frame in self.cache:
            self.stats['cache_hits'] += 1
            self.cache.move_to_end(frame)
            return self.cache[frame]
        started = time.perf_counter()
        try:
            position = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            if 0 <= frame - position <= 12:
                for _ in range(round(frame - position)):
                    self.stats['grabs'] += 1
                    if not self.cap.grab():
                        raise ValueError('source_frame_unavailable')
            else:
                self.stats['seeks'] += 1
                if not self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame):
                    raise ValueError('source_seek_failed')
            if abs(self.cap.get(cv2.CAP_PROP_POS_FRAMES) - frame) > .1:
                raise ValueError('source_position_mismatch')
            ok, image = self.cap.read()
            self.stats['reads'] += 1
            if not ok or abs(self.cap.get(cv2.CAP_PROP_POS_FRAMES) - frame - 1) > .1:
                raise ValueError('source_frame_unavailable')
        finally:
            self.stats['decode_seconds'] += time.perf_counter() - started
        image.flags.writeable = False
        if image.nbytes <= self.max_bytes:
            while self.cache and self.retained_bytes + image.nbytes > self.max_bytes:
                self.retained_bytes -= self.cache.popitem(last=False)[1].nbytes
            self.cache[frame] = image
            self.retained_bytes += image.nbytes
        return image

    def close(self):
        self.cap.release()
        self.cache.clear()
        self.retained_bytes = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
