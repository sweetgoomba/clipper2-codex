import os,tempfile,json,hashlib
from pathlib import Path
from types import SimpleNamespace
from dataclasses import asdict
import numpy as np
from clipper_accelerators import runtime,environment
from clipper_accelerators.cache import SelectionCache
from clipper_accelerators.contracts import Measurement
from clipper_accelerators.verification import finish_measurements
root=Path(tempfile.mkdtemp(prefix='policy-',dir='/private/tmp/clipper-reaudit-20261103/model'));os.environ['CLIPPER_ACCELERATOR_HOME']=str(root)
environment.native_environment=lambda *a:environment.probe_environment({'system':'darwin','host_arch':'arm64','process_arch':'arm64','os_build':'14'})
cache=SelectionCache(root/'measurements');key='b'*64;cache.quarantine(key,'quality_failed');row=Measurement(key,'complete',True,1,0,1,1,0,30,'env')
report={'mode':'verify','models':[{'measurement_key':key,'gpu_calls':33,'samples':33,'distinct_inputs':24,'pending_measurements':[asdict(row)],'release_qualified':False}]}
finish_measurements(report,{'status':'PASS'})
f06={'successful_explicit_recheck_available':cache.read(key) is not None,'release_qualified':report['models'][0]['release_qualified']}
cache.quarantine(key,'quality_failed');report['models'][0].update(distinct_inputs=1,pending_measurements=[asdict(row)])
finish_measurements(report,{'status':'PASS'});f06['incomplete_recheck_still_quarantined']=cache.read(key) is None
runtime.configure({'acceleration_mode':'verify'},'cpu',root)
remote=SimpleNamespace(profile_verified=True,graph_execution='mixed',provider_node_counts={'CPUExecutionProvider':7,'CoreMLExecutionProvider':3})
operation=lambda x:x;operation.acceleration_remote=remote
gate=runtime.ModelGate('face.yunet','s','dance','original','full_frame',lambda x:x,lambda:operation,backend='ort_coreml');gate.candidate=operation;gate.used_candidate=True
r=gate.report();f09={k:r[k] for k in ['execution_evidence','profile_verified','graph_execution','provider_node_counts','physical_gpu_verified']}
f09['legacy_provider_only']=runtime.NativeRecord('face.sface','CoreMLExecutionProvider','existing_runtime').report()['execution_evidence']
wall=[0.];runtime.time=SimpleNamespace(perf_counter=lambda:wall[0],monotonic=lambda:wall[0]);runtime.configure({'acceleration_mode':'verify'},'cpu',root)
def slow_cpu(x):wall[0]+=35.;return x
opened=[]
gate=runtime.ModelGate('pose.yolov8s','s','dance','original','frame',slow_cpu,lambda:opened.append(1) or (lambda x:x))
gate(np.ones((1,2),np.float32))
f05={'actual_simulated_comparison_seconds':wall[0],'per_model_budget_seconds':30,'reported_consumed_global_seconds':runtime._state['calibration_seconds'],'gate_trial_seconds':gate.trial_seconds,'reason':gate.reason,'candidate_calls':len(opened)}
result={'F06':f06,'F09':f09,'F05_remaining_cpu_budget_accounting':f05}
(root/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));print(root)
