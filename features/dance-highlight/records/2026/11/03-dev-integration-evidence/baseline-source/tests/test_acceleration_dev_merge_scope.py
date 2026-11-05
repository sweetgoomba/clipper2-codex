"""Merge scope: retain remote native CPU faces and gate only new adapters."""
from types import SimpleNamespace
import sys
import numpy as np
import pytest
from clipper_accelerators import runtime

@pytest.fixture(autouse=True)
def isolated(monkeypatch,tmp_path):
    old=dict(runtime._state)
    for key,value in [('CLIPPER_ACCELERATOR_MODE','auto'),('CLIPPER_ACCELERATOR_CONSUMER','dance'),('CLIPPER_ACCELERATOR_NATIVE_INTERPRETER',sys.executable),('CLIPPER_ACCELERATOR_HOME',str(tmp_path/'home'))]:monkeypatch.setenv(key,value)
    for key in ('CLIPPER_ACCELERATOR_HOST_URL','CLIPPER_ACCELERATOR_BUNDLE','CLIPPER_ACCELERATOR_CERTIFICATES','CLIPPER_ACCELERATORS_CPU_ONLY','CLIPPER_ACCELERATOR_TEST_PLAN'):monkeypatch.delenv(key,raising=False)
    yield
    runtime._state.clear();runtime._state.update(old)


def fake_models(monkeypatch,tmp_path):
    import cv2,onnxruntime as ort
    from dance_highlight.services import face_models,face_cluster
    from clipper_face_core.face_models import AURAFACE_MODEL_NAME
    detector=object();created=[]
    paths={AURAFACE_MODEL_NAME:tmp_path/'aura.onnx','opencv-yunet-face-detection':tmp_path/'yunet.onnx'}
    for path in paths.values():path.write_bytes(b'model')
    monkeypatch.setattr(face_cluster,'ensure_face_models',lambda:paths)
    monkeypatch.setattr(face_cluster,'read_model_buffer',lambda _:np.zeros(1,np.uint8))
    monkeypatch.setattr(face_models,'sha256_file',lambda _:'hash')
    monkeypatch.setattr(cv2,'FaceDetectorYN',SimpleNamespace(create=lambda *a:detector))
    monkeypatch.setattr(ort,'get_available_providers',lambda:['CoreMLExecutionProvider','DmlExecutionProvider','CPUExecutionProvider'])
    class Session:
        def __init__(self,path,*,providers,sess_options=None):self.providers=[p[0] if isinstance(p,tuple) else p for p in providers];created.append(self)
        def get_inputs(self):return [SimpleNamespace(name='input',shape=[None,3,112,112])]
        def get_outputs(self):return [SimpleNamespace(name='out')]
        def get_providers(self):return self.providers
        def run(self,*args):return [np.ones((1,512),np.float32)]
    monkeypatch.setattr(ort,'InferenceSession',Session)
    return detector,created


def test_unapproved_auto_keeps_remote_cpu_faces(monkeypatch,tmp_path):
    from dance_highlight.services.face_cluster import FaceClusterService
    detector,created=fake_models(monkeypatch,tmp_path)
    config=SimpleNamespace(face_det_size=(320,320),face_min_det_score=.6,face_nms_threshold=.3,face_top_k=5000)
    service=FaceClusterService(config)
    assert service._recognizer._session.get_providers()==['CPUExecutionProvider']
    assert service._detector is detector
    assert all(row.providers==['CPUExecutionProvider'] for row in created)


def test_forced_cpu_reference_does_not_enter_optional_routes(monkeypatch,tmp_path):
    from dance_highlight.services.face_cluster import FaceClusterService
    detector,created=fake_models(monkeypatch,tmp_path)
    def forbidden(*a,**kw):raise AssertionError('CPU reference must not route an optional backend')
    monkeypatch.setattr('clipper_accelerators.face_adapter.route_detector',forbidden)
    monkeypatch.setenv('CLIPPER_ACCELERATOR_MODE','verify')
    config=SimpleNamespace(face_det_size=(320,320),face_min_det_score=.6,face_nms_threshold=.3,face_top_k=5000)
    service=FaceClusterService(config,cpu_only=True)
    assert service._detector is detector
    assert all(row.providers==['CPUExecutionProvider'] for row in created)


def test_runtime_reports_user_disabled_sam_and_pipeline_has_no_tracking_calls():
    from dance_highlight.app import DanceHighlightPlugin
    plugin=DanceHighlightPlugin();plugin._device='mps'
    plugin._pipeline=SimpleNamespace(face=None)
    tracking=plugin.get_runtime_accelerators().get('models',{}).get('body_tracking',{})
    assert tracking.get('enabled') is False
    assert tracking.get('reason')=='disabled_runtime_cost'
    import ast, inspect
    from dance_highlight.services import pipeline
    calls={node.func.id for node in ast.walk(ast.parse(inspect.getsource(pipeline)))
           if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)}
    assert not calls & {'recover_mask_names','revalidate_named_segments'}


@pytest.mark.parametrize('consumer',['cut','sampled'])
def test_both_sface_consumers_enter_shared_admission(monkeypatch,tmp_path,consumer):
    import cv2
    from dance_highlight.services import face_cluster,face_models
    from dance_highlight.services.cut_face_link import CutFaceLink
    from dance_highlight.services.sampled_face_link import SampledFaceLink
    native=object();routed=object();calls=[]
    service=SimpleNamespace(_detector=object(),_recognizer=object(),cpu_only=False,
        config=SimpleNamespace(face_min_det_score=.6),model_provenance={})
    monkeypatch.setattr(face_cluster,'FaceClusterService',lambda *a:service)
    monkeypatch.setattr(face_models,'ensure_face_models',lambda **kw:{kw['specs'][0].name:tmp_path/'sface.onnx'})
    monkeypatch.setattr(face_models,'read_model_buffer',lambda _:np.zeros(1,np.uint8))
    monkeypatch.setattr(face_models,'sha256_file',lambda _:'hash')
    monkeypatch.setattr(cv2,'FaceRecognizerSF',SimpleNamespace(create=lambda *a:native))
    monkeypatch.setattr('clipper_accelerators.face_adapter.route_recognizer',lambda obj,path,**kw:calls.append((obj,path,kw)) or routed)
    result=CutFaceLink(face_service=service) if consumer=='cut' else SampledFaceLink()
    assert result.secondary is routed
    assert calls==[(native,tmp_path/'sface.onnx',{})]
