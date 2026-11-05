"""Dance-only AuraFace acceleration; shared/person defaults stay on CPU."""
from collections import OrderedDict
import hashlib
import logging
import os
from pathlib import Path
import platform
import threading
import time

import numpy as np
import onnxruntime as ort
import cv2

from clipper_face_core.face_models import AURAFACE_SHA256

logger = logging.getLogger(__name__)


def configure_cpu_threads():
    """Restore CPU face parallelism in the isolated Dance plugin process.

    Ultralytics disables OpenCV threads for its data loaders. This plugin
    calls models sequentially and has no data-loader workers. GCD delegates
    its pool to macOS; getNumThreads reports that pool, not a hard limit.
    """
    backend = next((line.split(':',1)[1].strip() for line in cv2.getBuildInformation().splitlines()
                    if 'Parallel framework:' in line), 'unknown')
    cpus = max(1, os.cpu_count() or 1)
    requested = (-1 if cpus > 1 else 0) if backend == 'GCD' else min(4, cpus)
    cv2.setNumThreads(requested)
    info = dict(backend=backend, requested_threads=requested, reported_threads=cv2.getNumThreads())
    logger.info('Dance OpenCV CPU parallelism=%s', info)
    return info


class CachedFaceDetector:
    """Reuse exact pixels at the same input size; detector parameters are fixed."""
    def __init__(self, detector, *, max_entries=8192, max_bytes=32 * 1024 * 1024):
        self.detector = detector
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.retained_bytes = 0
        self.request = threading.local()
        self.lock = threading.Lock()
        self.cache = OrderedDict()
        self.stats = dict(requests=0, cache_hits=0, detection_seconds=0.)

    def setInputSize(self, size):
        self.request.size = tuple(size)

    def prepare_source(self, size):
        with self.lock:
            self.detector.prepare_source(size)

    @staticmethod
    def _key(image, size):
        return (size, image.shape, image.dtype.str,
                hashlib.sha256(np.ascontiguousarray(image)).digest())

    def detect(self, image):
        with self.lock:
            return self._detect(image)

    def _detect(self, image):
        self.stats['requests'] += 1
        size = getattr(self.request, 'size', None)
        key = self._key(image,size)
        if key in self.cache:
            self.stats['cache_hits'] += 1
            self.cache.move_to_end(key)
            status, faces = self.cache[key]
            return status, None if faces is None else faces.copy()
        started = time.perf_counter()
        if size is not None:
            self.detector.setInputSize(size)
        try:
            status, faces = self.detector.detect(image)
        finally:
            self.stats['detection_seconds'] += time.perf_counter() - started
        self.cache[key] = status, None if faces is None else faces.copy()
        self.retained_bytes += 0 if faces is None else faces.nbytes
        while self.cache and (len(self.cache) > self.max_entries or self.retained_bytes > self.max_bytes):
            _, (_, removed) = self.cache.popitem(last=False)
            self.retained_bytes -= 0 if removed is None else removed.nbytes
        return status, faces


class DanceFaceSession:
    """One model session with bounded exact-input reuse and CPU recovery."""
    def __init__(self, model_path, *, providers=None):
        self.model_path = str(model_path)
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.stats = dict(requests=0, inferences=0, cache_hits=0, fallbacks=0, inference_seconds=0.)
        available = ort.get_available_providers()
        options = ort.SessionOptions()
        requested = ['CPUExecutionProvider']
        system = platform.system()
        if system == 'Darwin' and 'CoreMLExecutionProvider' in available:
            cache = Path(model_path).parent / 'coreml-cache' / AURAFACE_SHA256
            requested.insert(0, ('CoreMLExecutionProvider', dict(
                ModelFormat='MLProgram', MLComputeUnits='CPUAndGPU',
                ModelCacheDirectory=str(cache), RequireStaticInputShapes='0')))
        elif system == 'Windows':
            if 'CUDAExecutionProvider' in available:
                requested.insert(0, ('CUDAExecutionProvider', {'use_tf32': '0'}))
            elif 'DmlExecutionProvider' in available:
                options.enable_mem_pattern = False
                options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                requested.insert(0, 'DmlExecutionProvider')
        started = time.perf_counter()
        try:
            self.session = ort.InferenceSession(self.model_path, sess_options=options, providers=requested)
            if self._accelerated():
                # Fail during loading, rather than the first user's reference image.
                self._validate(self.session.run([self.get_outputs()[0].name],
                    {self.get_inputs()[0].name: np.zeros((1, 3, 112, 112), np.float32)}))
        except Exception:
            if len(requested) == 1:
                raise
            self._fallback()
        self.stats['setup_seconds'] = time.perf_counter() - started
        logger.info('Dance AuraFace providers=%s', self.get_providers())

    def _accelerated(self):
        return any(p != 'CPUExecutionProvider' for p in self.session.get_providers())

    def _fallback(self):
        logger.warning('Dance AuraFace GPU unavailable; retrying with CPU', exc_info=True)
        self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
        self.cache.clear()
        self.stats['fallbacks'] += 1

    @staticmethod
    def _validate(outputs):
        if len(outputs) != 1 or outputs[0].shape != (1, 512) or not np.isfinite(outputs[0]).all():
            raise ValueError('Invalid AuraFace embedding')

    def get_inputs(self):
        return self.session.get_inputs()

    def get_outputs(self):
        return self.session.get_outputs()

    def get_providers(self):
        return self.session.get_providers()

    def run(self, outputs, inputs):
        # DirectML forbids concurrent Run on one session. Also protect fallback/cache.
        with self.lock:
            return self._run(outputs, inputs)

    def _run(self, outputs, inputs):
        self.stats['requests'] += 1
        key = (tuple(outputs), tuple((name, value.shape, value.dtype.str,
            hashlib.sha256(np.ascontiguousarray(value)).digest()) for name, value in inputs.items()))
        if key in self.cache:
            self.stats['cache_hits'] += 1
            self.cache.move_to_end(key)
            return [value.copy() for value in self.cache[key]]
        started = time.perf_counter()
        try:
            try:
                result = self.session.run(outputs, inputs)
                self._validate(result)
            except Exception:
                if not self._accelerated():
                    raise
                self._fallback()
                result = self.session.run(outputs, inputs)
                self._validate(result)
        finally:
            self.stats['inferences'] += 1
            self.stats['inference_seconds'] += time.perf_counter() - started
        self.cache[key] = [value.copy() for value in result]
        # At most 8 MiB of 512-float embeddings, plus keys/container overhead.
        if len(self.cache) > 4096:
            self.cache.popitem(last=False)
        return result
