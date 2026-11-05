"""Keep existing face pixels/decisions when replacing only the inference engine."""
from types import SimpleNamespace

import cv2
import numpy as np
import onnx
import pytest
from onnx import TensorProto, helper, numpy_helper


def test_prepared_model_keeps_weights_and_ops_and_removes_stale_shapes(tmp_path):
    from dance_highlight.services.opencv_acceleration import prepare_model
    weight = numpy_helper.from_array(np.ones((1,), np.float32), 'weight')
    graph = helper.make_graph([helper.make_node('Add', ['input', 'weight'], ['cls_8'])], 'g',
        [helper.make_tensor_value_info('input', TensorProto.FLOAT, [1, 3, 640, 640]),
         helper.make_tensor_value_info('weight', TensorProto.FLOAT, [1])],
        [helper.make_tensor_value_info('cls_8', TensorProto.FLOAT, [1, 6400, 1])], [weight],
        value_info=[helper.make_tensor_value_info('obsolete', TensorProto.FLOAT, [640])])
    path = tmp_path/'한글 모델.onnx'
    onnx.save(helper.make_model(graph), path)
    original = path.read_bytes()
    prepared = onnx.load_model_from_string(prepare_model(path, spatial_size=(1920, 1088)))
    assert path.read_bytes() == original
    assert prepared.graph.initializer[0].SerializeToString() == weight.SerializeToString()
    assert [n.SerializeToString() for n in prepared.graph.node] == [n.SerializeToString() for n in graph.node]
    assert [v.name for v in prepared.graph.input] == ['input']
    assert [d.dim_value for d in prepared.graph.input[0].type.tensor_type.shape.dim] == [1,3,1088,1920]
    assert not any(v.name == 'obsolete' for v in prepared.graph.value_info)


def _outputs():
    # A single 32x32 padded image, with anchors at strides 8,16,32.
    values = {}
    for stride,n in ((8,16),(16,4),(32,1)):
        for key,c in (('cls',1),('obj',1),('bbox',4),('kps',10)):
            values[f'{key}_{stride}'] = np.zeros((1,n,c), np.float32)
    values['cls_8'][0,5,0] = 1.2  # Clamp to 1; sqrt(1 * .81) = .9.
    values['obj_8'][0,5,0] = .81
    values['bbox_8'][0,5] = [.25,.5,0,0]
    values['kps_8'][0,5] = [.25,.5,.5,.5,.5,.75,0,1,1,1]
    return values


def test_yunet_decodes_stride_centers_landmarks_and_clamped_scores():
    from dance_highlight.services.opencv_acceleration import decode_yunet
    faces = decode_yunet(_outputs(), (32,32), .28,.3,5000)
    np.testing.assert_allclose(faces, [[6,8,8,8,10,12,12,12,12,14,8,16,16,16,.9]], atol=1e-6)


def test_yunet_empty_results_and_invalid_outputs_are_not_false_faces():
    from dance_highlight.services.opencv_acceleration import decode_yunet
    values=_outputs()
    assert decode_yunet(values,(32,32),.95,.3,5000) is None
    values['bbox_8'][0,5,0]=np.nan
    with pytest.raises(ValueError): decode_yunet(values,(32,32),.28,.3,5000)


def test_yunet_nms_uses_integer_boxes_like_opencv():
    from dance_highlight.services.opencv_acceleration import decode_yunet
    values=_outputs()
    # Boxes x=6 and x=10.9, w=8: float IoU .24, integer IoU .333.
    values['cls_8'][0,6,0]=.8
    values['obj_8'][0,6,0]=1
    values['bbox_8'][0,6]=[-.1375,.5,0,0]
    faces=decode_yunet(values,(32,32),.28,.3,5000)
    assert len(faces)==1
    assert faces[0,0]==6


@pytest.mark.parametrize('system,available,expected', [
    ('Darwin',['CoreMLExecutionProvider'],'CoreMLExecutionProvider'),
    ('Windows',['DmlExecutionProvider'],'DmlExecutionProvider'),
    ('Windows',['CUDAExecutionProvider','DmlExecutionProvider'],'CUDAExecutionProvider'),
    ('Linux',['CPUExecutionProvider'],None),
])
def test_provider_selection_preserves_precision_and_windows_execution_rules(tmp_path, system, available, expected):
    from dance_highlight.services.opencv_acceleration import accelerator_options
    requested,options=accelerator_options(tmp_path,system=system,available=available)
    if expected is None:
        assert requested==[]
    else:
        assert requested[0][0]==expected
        assert requested[-1]=='CPUExecutionProvider'
        settings=requested[0][1]
        if system=='Darwin':
            assert settings['MLComputeUnits']=='CPUAndGPU'
            assert settings['AllowLowPrecisionAccumulationOnGPU']=='0'
        elif expected=='DmlExecutionProvider':
            import onnxruntime as ort
            assert options.execution_mode==ort.ExecutionMode.ORT_SEQUENTIAL
            assert not options.enable_mem_pattern
        else:
            assert settings['use_tf32']=='0'


class NativeDetector:
    def setInputSize(self,size): self.size=size
    def detect(self,image): return 1,np.full((1,15),42,np.float32)


@pytest.fixture
def fake_gpu(monkeypatch):
    # Synthetic session tests must work on CPU-only CI as well as this Mac.
    monkeypatch.setattr('platform.system', lambda:'Darwin')
    monkeypatch.setattr('onnxruntime.get_available_providers', lambda:['CoreMLExecutionProvider','CPUExecutionProvider'])


def test_yunet_only_accelerates_source_shape_without_resizing(monkeypatch,tmp_path,fake_gpu):
    from dance_highlight.services import opencv_acceleration as runtime
    blobs=[]
    class Session:
        def __init__(self,*args,**kwargs): pass
        def run(self,blob):
            blobs.append(blob.copy())
            return _outputs()
        def status(self): return {'providers':['DmlExecutionProvider']}
    monkeypatch.setattr(runtime,'AcceleratedSession',Session)
    detector=runtime.AcceleratedYuNet(NativeDetector(),tmp_path/'model.onnx',.28,.3,5000)
    detector.prepare_source((31,30))
    image=np.full((30,31,3),[13,53,201],np.uint8)
    detector.setInputSize((31,30)); result=detector.detect(image)[1]
    assert result[0,0]==6
    blob=blobs[-1]
    assert blob.shape==(1,3,32,32)
    np.testing.assert_array_equal(blob[0,:,0,0],[13,53,201])
    assert not blob[:,:,30:,:].any() and not blob[:,:,:,31:].any()
    count=len(blobs)
    detector.setInputSize((20,20))
    np.testing.assert_array_equal(detector.detect(image[:20,:20])[1],np.full((1,15),42))
    assert len(blobs)==count  # No session/compile per ROI shape.


@pytest.mark.parametrize('invalid',[False,True])
def test_yunet_falls_back_permanently_after_failed_or_invalid_gpu_result(monkeypatch,tmp_path,invalid,fake_gpu):
    from dance_highlight.services import opencv_acceleration as runtime
    calls=[]
    class Session:
        def __init__(self,*args,**kwargs): pass
        def run(self,blob):
            calls.append(1)
            if not invalid: raise RuntimeError('GPU failed')
            values=_outputs();values['bbox_8'][0,5,0]=np.nan;return values
        def status(self): return {'providers':['DmlExecutionProvider']}
    monkeypatch.setattr(runtime,'AcceleratedSession',Session)
    detector=runtime.AcceleratedYuNet(NativeDetector(),tmp_path/'model.onnx',.28,.3,5000)
    detector.prepare_source((32,32));detector.setInputSize((32,32))
    for _ in range(2):
        np.testing.assert_array_equal(detector.detect(np.zeros((32,32,3),np.uint8))[1],np.full((1,15),42))
    assert len(calls)==1
    assert detector.status()['fallbacks']==1
    assert detector.status()['providers']==['OpenCVCPU']


def test_sface_retains_opencv_alignment_and_rgb_unscaled_pixels(monkeypatch,tmp_path,fake_gpu):
    from dance_highlight.services import opencv_acceleration as runtime
    crop=np.full((112,112,3),[13,53,201],np.uint8)
    native=SimpleNamespace(alignCrop=lambda image,face:crop,feature=lambda crop:np.full((1,128),42))
    seen=[]
    class Session:
        def __init__(self,*args,**kwargs): pass
        def run(self,blob):
            seen.append(blob.copy());return {'fc1':np.ones((1,128),np.float32)}
        def status(self): return {'providers':['CoreMLExecutionProvider']}
    monkeypatch.setattr(runtime,'AcceleratedSession',Session)
    recognizer=runtime.AcceleratedSFace(native,tmp_path/'model.onnx')
    aligned=recognizer.alignCrop(None,None)
    assert aligned is crop
    np.testing.assert_array_equal(recognizer.feature(aligned),np.ones((1,128)))
    np.testing.assert_array_equal(seen[-1][0,:,0,0],[201,53,13])


def test_sface_invalid_embedding_uses_original_cpu_and_stops_retrying(monkeypatch,tmp_path,fake_gpu):
    from dance_highlight.services import opencv_acceleration as runtime
    calls=[]
    class Session:
        def __init__(self,*args,**kwargs): pass
        def run(self,blob): calls.append(1);return {'fc1':np.full((1,128),np.nan)}
        def status(self): return {'providers':['DmlExecutionProvider']}
    monkeypatch.setattr(runtime,'AcceleratedSession',Session)
    native=SimpleNamespace(feature=lambda crop:np.full((1,128),42))
    recognizer=runtime.AcceleratedSFace(native,tmp_path/'model.onnx')
    for _ in range(2):
        np.testing.assert_array_equal(recognizer.feature(np.zeros((112,112,3),np.uint8)),np.full((1,128),42))
    assert len(calls)==1
    assert recognizer.status()['providers']==['OpenCVCPU']


def test_runtime_reports_actual_detection_and_secondary_fallback():
    from dance_highlight.app import DanceHighlightPlugin
    detector=SimpleNamespace(status=lambda:{'providers':['CoreMLExecutionProvider','CPUExecutionProvider'],
                                            'source_size':(1920,1080), 'fallbacks':0})
    secondary=SimpleNamespace(status=lambda:{'providers':['OpenCVCPU'],'fallbacks':1})
    face=SimpleNamespace(_detector=SimpleNamespace(detector=detector),_secondary_recognizer=secondary)
    plugin=DanceHighlightPlugin();plugin._pipeline=SimpleNamespace(face=face)
    info=plugin.get_runtime_accelerators()['models']
    assert info['face_detection']['providers'][0]=='CoreMLExecutionProvider'
    assert info['secondary_face']['providers']==['OpenCVCPU']
    assert info['secondary_face']['fallbacks']==1
    assert info['body_tracking']['enabled'] is False


def test_cached_detector_forwards_source_setup_under_its_lock():
    from dance_highlight.services.face_runtime import CachedFaceDetector
    sizes=[]
    native=NativeDetector();native.prepare_source=lambda size:sizes.append(size)
    detector=CachedFaceDetector(native)
    detector.prepare_source((1920,1080))
    assert sizes==[(1920,1080)]
