import subprocess
import sys


def probe(statement, blocked):
    code='''import importlib.abc,sys
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in sys.argv[1].split(','): raise ImportError('blocked '+fullname)
sys.meta_path.insert(0,Block())
'''+statement
    return subprocess.run([sys.executable,'-c',code,blocked],text=True,capture_output=True)


def test_sdk_starts_without_ml():
    r=probe('import clipper_plugin_sdk','numpy,cv2,torch,onnxruntime')
    assert r.returncode==0,r.stderr


def test_core_types_without_opencv():
    r=probe('from clipper_face_core import FaceDetection, ModelFiles, build_gallery, match_reference, combine_reference_matches; from clipper_face_core.contracts import MatchPolicy','cv2,torch,onnxruntime')
    assert r.returncode==0,r.stderr


def test_explicit_backend_without_opencv_explains_optional_dependency():
    r=probe('from clipper_face_core import OpenCvFaceBackend','cv2')
    assert r.returncode!=0
    assert 'clipper-face-core[opencv]' in r.stderr
