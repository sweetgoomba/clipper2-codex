"""Dance-only inference adapters for the existing YuNet and SFace weights.

YuNet's full source frame has a stable shape; compile that shape once. Crops
keep OpenCV so changing ROI sizes cannot trigger repeated CoreML compilation.
Alignment, pixels, model weights and decision thresholds remain unchanged.
"""
import hashlib
import logging
from pathlib import Path
import platform
import threading
import time

import cv2
import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)


def prepare_model(path, *, spatial_size=None):
    import onnx
    model = onnx.load_model_from_string(Path(path).read_bytes())
    # These are constants, not overridable inputs. SFace's older export lists
    # both, preventing ORT from folding constants / assigning convolutions.
    constants = {value.name for value in model.graph.initializer}
    inputs = [value for value in model.graph.input if value.name not in constants]
    del model.graph.input[:]
    model.graph.input.extend(inputs)
    if spatial_size is not None:
        width, height = spatial_size
        dims = model.graph.input[0].type.tensor_type.shape.dim
        dims[2].dim_value, dims[3].dim_value = height, width
        # Original metadata describes 640x640, while OpenCV accepts native
        # dimensions. Remove stale intermediate shapes and infer the same ops.
        del model.graph.value_info[:]
        for value in model.graph.output:
            stride = int(value.name.rsplit('_', 1)[1])
            value.type.tensor_type.shape.dim[1].dim_value = (height // stride) * (width // stride)
        model = onnx.shape_inference.infer_shapes(model)
    return model.SerializeToString()


def accelerator_options(cache_path, *, system=None, available=None):
    system = platform.system() if system is None else system
    available = ort.get_available_providers() if available is None else available
    options = ort.SessionOptions()
    options.log_severity_level = 3
    options.intra_op_num_threads = 4
    provider = None
    if system == 'Darwin' and 'CoreMLExecutionProvider' in available:
        provider = ('CoreMLExecutionProvider', {
            'ModelFormat': 'MLProgram', 'MLComputeUnits': 'CPUAndGPU',
            'RequireStaticInputShapes': '1', 'AllowLowPrecisionAccumulationOnGPU': '0',
            'ModelCacheDirectory': str(cache_path),
        })
    elif system == 'Windows':
        if 'CUDAExecutionProvider' in available:
            provider = ('CUDAExecutionProvider', {'use_tf32': '0'})
        elif 'DmlExecutionProvider' in available:
            provider = ('DmlExecutionProvider', {})
            options.enable_mem_pattern = False
            options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    return ([provider, 'CPUExecutionProvider'] if provider else []), options


class AcceleratedSession:
    def __init__(self, path, *, spatial_size=None):
        data = prepare_model(path, spatial_size=spatial_size)
        digest = hashlib.sha256(data).hexdigest()
        providers, options = accelerator_options(Path(path).parent / 'coreml-cache' / 'opencv-v1' / digest)
        if not providers:
            raise RuntimeError('No compatible face accelerator')
        self.session = ort.InferenceSession(data, sess_options=options, providers=providers)
        if not any(p != 'CPUExecutionProvider' for p in self.session.get_providers()):
            raise RuntimeError('Face accelerator initialization fell back to CPU')
        self.input_name = self.session.get_inputs()[0].name
        self.outputs = [value.name for value in self.session.get_outputs()]

    def run(self, blob):
        # Callers lock the whole operation, including fallback. DirectML does
        # not support concurrent Run calls on the same inference session.
        return dict(zip(self.outputs, self.session.run(self.outputs, {self.input_name: blob}), strict=True))

    def status(self):
        return {'providers': self.session.get_providers()}


def decode_yunet(outputs, padded_size, score_threshold, nms_threshold, top_k):
    """OpenCV FaceDetectorYN decoding, including Rect2i NMS (4.13 behavior)."""
    width, height = padded_size
    candidates = []
    for stride in (8, 16, 32):
        cols, rows = width // stride, height // stride
        count = cols * rows
        values = []
        for key, channels in (('cls',1), ('obj',1), ('bbox',4), ('kps',10)):
            value = outputs[f'{key}_{stride}']
            if value.shape != (1,count,channels) or not np.isfinite(value).all():
                raise ValueError('Invalid YuNet output')
            values.append(value.reshape(count,channels))
        cls, obj, box, points = values
        scores = np.sqrt(np.clip(cls[:,0],0,1) * np.clip(obj[:,0],0,1))
        indices = np.flatnonzero(scores >= score_threshold)
        if not len(indices):
            continue
        grid = np.column_stack((indices % cols, indices // cols)).astype(np.float32)
        sizes = np.exp(box[indices,2:]) * stride
        centers = (box[indices,:2] + grid) * stride
        landmarks = ((points[indices].reshape(-1,5,2) + grid[:,None,:]) * stride).reshape(-1,10)
        faces = np.column_stack((centers - sizes / 2, sizes, landmarks, scores[indices])).astype(np.float32)
        if not np.isfinite(faces).all():
            raise ValueError('Invalid decoded YuNet face')
        candidates.append(faces)
    if not candidates:
        return None
    faces = np.concatenate(candidates)
    if len(faces) > 1:
        boxes = faces[:,:4].astype(np.int32).tolist()  # C++ casts truncate toward zero.
        keep = cv2.dnn.NMSBoxes(boxes, faces[:,14].tolist(), score_threshold,
                               nms_threshold, eta=1., top_k=top_k)
        if not len(keep):
            return None
        faces = faces[np.asarray(keep).reshape(-1)]
    return faces


class AcceleratedYuNet:
    def __init__(self, native, model_path, score_threshold, nms_threshold, top_k):
        self.native, self.model_path = native, Path(model_path)
        self.thresholds = score_threshold, nms_threshold, top_k
        self.source_size = self.input_size = None
        self.session = None
        self.lock = threading.Lock()
        self.failed = False
        self.stats = dict(gpu_calls=0, cpu_calls=0, fallbacks=0, setup_seconds=0., gpu_seconds=0.)

    def prepare_source(self, size):
        with self.lock:
            size = tuple(size)
            if size == self.source_size or self.failed:
                return
            self.source_size = size
            self.session = None  # At most one source resolution/session per service.
            if not accelerator_options(self.model_path.parent)[0]:
                return
            started = time.perf_counter()
            try:
                self.session = AcceleratedSession(self.model_path, spatial_size=self._padded(size))
            except Exception:
                self._fallback()
            finally:
                self.stats['setup_seconds'] += time.perf_counter() - started

    @staticmethod
    def _padded(size):
        return tuple((int(v) + 31) // 32 * 32 for v in size)

    def _fallback(self):
        logger.warning('Dance YuNet accelerator unavailable; using OpenCV CPU', exc_info=True)
        self.session = None
        self.failed = True
        self.stats['fallbacks'] += 1

    def setInputSize(self, size):
        self.input_size = tuple(size)
        self.native.setInputSize(size)

    def detect(self, image):
        with self.lock:
            size = (image.shape[1], image.shape[0])
            if self.session is not None and size == self.source_size == self.input_size:
                started = time.perf_counter()
                try:
                    width,height = self._padded(size)
                    padded = cv2.copyMakeBorder(image,0,height-size[1],0,width-size[0],cv2.BORDER_CONSTANT)
                    outputs = self.session.run(cv2.dnn.blobFromImage(padded))
                    faces = decode_yunet(outputs,(width,height),*self.thresholds)
                    self.stats['gpu_calls'] += 1
                    return 1,faces
                except Exception:
                    self._fallback()
                finally:
                    self.stats['gpu_seconds'] += time.perf_counter()-started
            self.stats['cpu_calls'] += 1
            return self.native.detect(image)

    def status(self):
        return {**(self.session.status() if self.session else {'providers':['OpenCVCPU']}),
                'mode':'source_frame_gpu_crops_cpu', 'source_size':self.source_size, **self.stats}


class AcceleratedSFace:
    def __init__(self, native, model_path):
        self.native = native
        self.lock = threading.Lock()
        self.session = None
        self.stats = dict(gpu_calls=0, cpu_calls=0, fallbacks=0, setup_seconds=0., gpu_seconds=0.)
        started = time.perf_counter()
        if accelerator_options(Path(model_path).parent)[0]:
            try:
                self.session = AcceleratedSession(model_path)
            except Exception:
                self._fallback()
        self.stats['setup_seconds'] = time.perf_counter()-started

    def _fallback(self):
        logger.warning('Dance SFace accelerator unavailable; using OpenCV CPU', exc_info=True)
        self.session = None
        self.stats['fallbacks'] += 1

    def alignCrop(self, image, face):
        return self.native.alignCrop(image, face)

    def feature(self, aligned):
        with self.lock:
            if self.session is not None:
                started = time.perf_counter()
                try:
                    # Same OpenCV SFace preprocessing: RGB float32, scale 1.
                    blob = cv2.dnn.blobFromImage(aligned,1.,(112,112),swapRB=True,crop=False)
                    result = self.session.run(blob)['fc1']
                    if result.shape != (1,128) or not np.isfinite(result).all():
                        raise ValueError('Invalid SFace embedding')
                    self.stats['gpu_calls'] += 1
                    return result
                except Exception:
                    self._fallback()
                finally:
                    self.stats['gpu_seconds'] += time.perf_counter()-started
            self.stats['cpu_calls'] += 1
            return self.native.feature(aligned)

    def status(self):
        return {**(self.session.status() if self.session else {'providers':['OpenCVCPU']}), **self.stats}


def secondary_recognizer(face_service, path):
    """One SFace session per Dance face service, shared by its verification passes."""
    recognizer = getattr(face_service, '_secondary_recognizer', None)
    if recognizer is None:
        from .face_models import read_model_buffer
        native = cv2.FaceRecognizerSF.create('onnx', read_model_buffer(path), np.empty(0,np.uint8))
        recognizer = AcceleratedSFace(native, path)
        face_service._secondary_recognizer = recognizer
    return recognizer


def runtime_status(face_service):
    detector = getattr(getattr(face_service, '_detector', None), 'detector', None)
    secondary = getattr(face_service, '_secondary_recognizer', None)
    return {
        'face_detection': detector.status() if hasattr(detector, 'status') else {'providers':['OpenCVCPU']},
        'secondary_face': secondary.status() if hasattr(secondary, 'status') else {'providers':[], 'state':'not_loaded'},
    }
