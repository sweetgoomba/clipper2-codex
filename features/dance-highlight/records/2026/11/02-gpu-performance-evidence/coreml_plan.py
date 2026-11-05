from pathlib import Path
import onnxruntime as ort,numpy as np
root=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/plugin_models/dance_highlight')
s=ort.SessionOptions();s.log_severity_level=0
sess=ort.InferenceSession(str(root/'glintr100.onnx'),sess_options=s,providers=[('CoreMLExecutionProvider',{'ModelFormat':'MLProgram','MLComputeUnits':'CPUAndGPU','ProfileComputePlan':'1','ModelCacheDirectory':'/private/tmp/dance-gpu-audit-20261102/coreml-cache'}),'CPUExecutionProvider'])
sess.run(None,{sess.get_inputs()[0].name:np.zeros((1,3,112,112),np.float32)})
print('compute plan check complete')
