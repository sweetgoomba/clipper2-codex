"""Bounded, lossless source reuse for one Dance SAM2 tracker."""
from collections import OrderedDict
from copy import deepcopy
import hashlib
from pathlib import Path
import cv2
import numpy as np

FEATURE_CACHE_BYTES = 512 * 1024 * 1024
REVERSE_DECODE_BYTES = 128 * 1024 * 1024


def verified_transitions(inventory, source, fps):
    """Reuse only a complete scan of this source, including all negative pairs."""
    if not inventory or not (inventory.get('reason') == 'complete'
            and inventory.get('source_path') == str(Path(source).resolve())
            and abs(inventory.get('fps', 0.) - fps) <= .001):
        return {}
    through = inventory.get('through_frame', -1)
    transitions = {d['frame']: {k: v for k, v in d.items() if k != 'frame'}
                   for d in inventory.get('camera_transitions', ())}
    if (set(inventory.get('cut_frames', ())) != {f for f, d in transitions.items() if d.get('cut')}
            or any(not 1 <= f <= through for f in transitions)):
        return {}
    return {f: deepcopy(transitions.get(f, dict(cut=False, color_candidate=False)))
            for f in range(1, through + 1)}


class SamMasks:
    """Lossless completed SAM sequences; length/order/prompts are part of identity.

    A shorter prefix is NOT equivalent: SAM uses num_frames in memory attention.
    No decoder memory or partial attempt is reused.
    """
    def __init__(self, *, max_bytes=128 * 1024 * 1024):
        self.max_bytes = max_bytes
        self.retained_bytes = 0
        self.items = OrderedDict()
        self.hits = self.misses = 0

    @staticmethod
    def _key(frames, prompts):
        return (tuple(frames), tuple((name, value.shape, value.dtype.str,
            hashlib.blake2b(value.tobytes(), digest_size=32).digest())
            for name, raw in sorted(prompts.items()) for value in (np.asarray(raw),)))

    def get(self, frames, prompts):
        key = self._key(frames, prompts)
        if key not in self.items:
            self.misses += 1
            return None
        self.hits += 1
        self.items.move_to_end(key)
        rows, _ = self.items[key]
        return (np.unpackbits(bits, count=int(np.prod(shape))).reshape(shape).astype(bool)
                for shape, bits in rows)

    def put(self, frames, prompts, masks):
        self.put_packed(frames, prompts, [(m.shape, np.packbits(m)) for m in masks])

    def put_packed(self, frames, prompts, rows):
        size = sum(bits.nbytes for _, bits in rows)
        if len(rows) != len(frames) or size > self.max_bytes:
            return
        key = self._key(frames, prompts)
        if key in self.items:
            self.retained_bytes -= self.items.pop(key)[1]
        while self.items and self.retained_bytes + size > self.max_bytes:
            self.retained_bytes -= self.items.popitem(last=False)[1][1]
        self.items[key] = rows, size
        self.retained_bytes += size


def source_frames(cap, frames, read, *, max_bytes=REVERSE_DECODE_BYTES):
    """Decode descending requests in ascending blocks, yield original order."""
    if len(frames) < 2 or frames[0] < frames[-1]:
        for frame in frames:
            yield read(cap, frame)
        return
    pixels = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) * int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * 3
    block_size = max(1, max_bytes // max(1, pixels))
    for start in range(0, len(frames), block_size):
        block = frames[start:start + block_size]
        try:
            images = {frame: read(cap, frame) for frame in reversed(block)}
        except (ValueError, cv2.error):
            # A later unreadable source frame must not preempt an earlier
            # ownership verdict. Recover the original lazy request order.
            for frame in block:
                yield read(cap, frame)
            continue
        try:
            for frame in block:
                yield images.pop(frame)
        finally:
            images.clear()


class SamImageFeatures:
    """Image features only: no prompt, object, mask or temporal memory.

    Owned by one fixed SAM2 model and one source. SAM2's sine positions are
    image-independent at a fixed shape/dtype/device; retain them once. Tensor
    precision is unchanged. Consumers must not mutate these image features.
    """
    def __init__(self, *, max_bytes=FEATURE_CACHE_BYTES):
        self.max_bytes = max_bytes
        self.signature = None
        self.frames = OrderedDict()
        self.positions = None
        self.retained_bytes = 0
        self.hits = self.misses = 0

    def get(self, frame, image, compute):
        signature = (tuple(image.shape), image.dtype, image.device)
        if signature != self.signature:
            self.frames.clear()
            self.positions = None
            self.retained_bytes = 0
            self.signature = signature
        if frame in self.frames:
            self.hits += 1
            self.frames.move_to_end(frame)
            features, sizes, _ = self.frames[frame]
            return features, self.positions, sizes
        self.misses += 1
        features, positions, sizes = compute()
        size = sum(t.numel() * t.element_size() for t in features)
        position_bytes = sum(t.numel() * t.element_size() for t in positions)
        if size + position_bytes > self.max_bytes:
            return features, positions, sizes
        if self.positions is None:
            self.positions = positions
            self.retained_bytes += position_bytes
        while self.frames and self.retained_bytes + size > self.max_bytes:
            _, (_, _, old_size) = self.frames.popitem(last=False)
            self.retained_bytes -= old_size
        self.frames[frame] = (features, sizes, size)
        self.retained_bytes += size
        return features, self.positions, sizes
