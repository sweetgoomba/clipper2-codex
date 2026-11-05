from types import SimpleNamespace

import numpy as np
import pytest

from clipper_face_core.auraface import AuraFaceRecognizer


@pytest.fixture
def runtime(monkeypatch):
    import onnxruntime as ort
    created = []

    class Session:
        def __init__(self, path, *, providers, sess_options=None):
            self.providers = [p[0] if isinstance(p, tuple) else p for p in providers]
            self.options = sess_options
            self.calls = 0
            self.fail = False
            self.invalid = False
            created.append(self)

        def get_inputs(self):
            return [SimpleNamespace(name='input', shape=[None, 3, 112, 112])]

        def get_outputs(self):
            return [SimpleNamespace(name='embedding')]

        def get_providers(self):
            return self.providers

        def run(self, outputs, inputs):
            self.calls += 1
            if self.fail:
                raise RuntimeError('GPU unavailable')
            value = float(next(iter(inputs.values())).mean())
            return [np.full((1, 512), np.nan if self.invalid else value, np.float32)]

    monkeypatch.setattr(ort, 'InferenceSession', Session)
    monkeypatch.setattr(ort, 'get_available_providers',
                        lambda: ['CoreMLExecutionProvider', 'DmlExecutionProvider', 'CPUExecutionProvider'])
    return created


@pytest.mark.parametrize('system,expected', [('Darwin','CoreMLExecutionProvider'),
                                          ('Windows','DmlExecutionProvider')])
def test_dance_uses_platform_gpu_with_cpu_fallback(monkeypatch, tmp_path, runtime, system, expected):
    from dance_highlight.services.face_runtime import DanceFaceSession
    monkeypatch.setattr('platform.system', lambda: system)
    model = tmp_path/'얼굴.onnx'; model.write_bytes(b'model')
    recognizer = AuraFaceRecognizer(model, session_factory=DanceFaceSession)
    result = recognizer.feature(np.full((112,112,3), 255, np.uint8))
    np.testing.assert_allclose(result, 1.)
    assert recognizer._session.get_providers() == [expected, 'CPUExecutionProvider']
    if system == 'Windows':
        import onnxruntime as ort
        assert runtime[0].options.enable_mem_pattern is False
        assert runtime[0].options.execution_mode == ort.ExecutionMode.ORT_SEQUENTIAL


def test_shared_recognizer_still_uses_cpu(monkeypatch, tmp_path, runtime):
    monkeypatch.setattr('platform.system', lambda: 'Darwin')
    recognizer = AuraFaceRecognizer(tmp_path/'model.onnx')
    recognizer.feature(np.full((112,112,3), 255, np.uint8))
    assert runtime[-1].providers == ['CPUExecutionProvider']


def test_missing_gpu_uses_cpu(monkeypatch, tmp_path, runtime):
    from dance_highlight.services.face_runtime import DanceFaceSession
    monkeypatch.setattr('onnxruntime.get_available_providers', lambda:['CPUExecutionProvider'])
    session = DanceFaceSession(str(tmp_path/'model.onnx'))
    assert session.get_providers() == ['CPUExecutionProvider']


@pytest.mark.parametrize('invalid', [False, True])
def test_gpu_failure_retries_on_cpu_and_reports_actual_provider(monkeypatch, tmp_path, runtime, invalid):
    from dance_highlight.services.face_runtime import DanceFaceSession
    monkeypatch.setattr('platform.system', lambda: 'Darwin')
    model=tmp_path/'model.onnx'; model.write_bytes(b'model')
    session=DanceFaceSession(str(model))
    if invalid:
        runtime[0].invalid=True
    else:
        runtime[0].fail=True
    result=session.run(['embedding'], {'input':np.ones((1,3,112,112),np.float32)})
    np.testing.assert_array_equal(result[0], np.ones((1,512),np.float32))
    assert session.get_providers() == ['CPUExecutionProvider']
    assert session.stats['fallbacks'] == 1


def test_identical_embeddings_reused_without_exposing_cached_arrays(monkeypatch, tmp_path, runtime):
    from dance_highlight.services.face_runtime import DanceFaceSession
    monkeypatch.setattr('onnxruntime.get_available_providers', lambda:['CPUExecutionProvider'])
    session=DanceFaceSession(str(tmp_path/'model.onnx'))
    blob=np.ones((1,3,112,112),np.float32)
    a=session.run(['embedding'],{'input':blob}); a[0][:]=99
    b=session.run(['embedding'],{'input':blob})
    np.testing.assert_array_equal(b[0], np.ones((1,512),np.float32))
    blob[:]=2
    c=session.run(['embedding'],{'input':blob})
    np.testing.assert_array_equal(c[0], np.full((1,512),2,np.float32))
    assert session.stats['cache_hits'] == 1
    assert session.stats['inferences'] == 2


def test_runtime_exposes_per_model_devices_instead_of_only_yolo():
    from dance_highlight.app import DanceHighlightPlugin
    plugin=DanceHighlightPlugin()
    plugin._device='mps'
    plugin._pipeline=SimpleNamespace(face=SimpleNamespace(_recognizer=SimpleNamespace(
        _session=SimpleNamespace(get_providers=lambda:['CPUExecutionProvider']))))
    info=plugin.get_runtime_accelerators()
    assert info['models']['pose']['device']=='mps'
    assert info['models']['face_recognition']['providers']==['CPUExecutionProvider']
    assert info['models']['body_tracking']['device']=='cpu'
    assert info['models']['body_tracking']['enabled'] is False
    assert info['models']['body_tracking']['reason']=='disabled_runtime_cost'


def test_concurrent_identical_requests_never_enter_one_session_twice(monkeypatch,tmp_path,runtime):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from dance_highlight.services.face_runtime import DanceFaceSession
    monkeypatch.setattr('onnxruntime.get_available_providers',lambda:['CPUExecutionProvider'])
    session=DanceFaceSession(str(tmp_path/'model.onnx'))
    entered,release,overlap=Event(),Event(),Event()
    original=runtime[0].run
    def run(outputs,inputs):
        if entered.is_set(): overlap.set()
        entered.set()
        assert release.wait(2)
        return original(outputs,inputs)
    runtime[0].run=run
    def request(): return session.run(['embedding'],{'input':np.ones((1,3,112,112),np.float32)})
    with ThreadPoolExecutor(2) as pool:
        first=pool.submit(request)
        assert entered.wait(2)
        second=pool.submit(request)
        concurrent=overlap.wait(.1)
        release.set()
        np.testing.assert_array_equal(first.result()[0],second.result()[0])
    assert not concurrent
    assert session.stats['inferences']==1


@pytest.mark.parametrize('backend,cpus,expected', [
    ('pthreads',1,1),('pthreads',2,2),('pthreads',10,4),('pthreads',None,1),
    ('GCD',10,-1),('GCD',1,0),('GCD',None,0)])
def test_dance_cpu_parallelism_respects_backend_and_available_cpus(monkeypatch, backend, cpus, expected):
    import cv2
    from dance_highlight.services import face_runtime
    monkeypatch.setattr('os.cpu_count', lambda:cpus)
    monkeypatch.setattr(cv2,'getBuildInformation',lambda:f'Parallel framework: {backend}')
    calls=[]
    monkeypatch.setattr(cv2,'setNumThreads',calls.append)
    info=face_runtime.configure_cpu_threads()
    assert calls==[expected]
    assert info['requested_threads']==expected
    assert info['backend']==backend


def test_dance_restores_face_parallelism_after_pose_initialization(monkeypatch):
    import cv2
    from dance_highlight import app
    previous=cv2.getNumThreads()
    monkeypatch.setattr('os.cpu_count',lambda:10)
    def pose(config):
        cv2.setNumThreads(1)
        return object()
    monkeypatch.setattr(app,'PoseEngine',pose)
    monkeypatch.setattr(app,'FaceClusterService',lambda config:SimpleNamespace())
    try:
        plugin=app.DanceHighlightPlugin()
        plugin.load_models()
        info=plugin.get_runtime_accelerators()
        cpu=info['models']['face_detection']['cpu_parallelism']
        assert cpu['requested_threads']==(-1 if cpu['backend']=='GCD' else 4)
        assert cpu['reported_threads']==cv2.getNumThreads()
        assert info['models']['secondary_face']['cpu_parallelism']==cpu
        assert info['models']['body_tracking']['enabled'] is False
    finally:
        cv2.setNumThreads(previous)
