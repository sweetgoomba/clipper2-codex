from pathlib import Path
from dataclasses import replace
import ast,importlib.util,json,sys
import numpy as np
from dance_highlight.services import segment as old
out=Path('/private/tmp/dance-role-continuity-review-20261102')
spec=importlib.util.spec_from_file_location('dance_highlight.services.proposed_segment',out/'proposed_segment.py')
new=importlib.util.module_from_spec(spec);sys.modules[spec.name]=new;spec.loader.exec_module(new)
node=next(x for x in ast.parse((out/'review_compact_scenes.py').read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='posed')
ns={'np':np,'old':old};exec(compile(ast.Module(body=[node],type_ignores=[]),'posed-fixture','exec'),ns);posed=ns['posed']
wide=posed([[820,500,870,730],[900,500,950,730],[980,500,1030,730],[300,500,350,730]])
wide.person_pose_keypoints[3][:,2]=.1
central=posed([[925,500,975,730]])
rows=[replace(central if .8<=i/10<1.1 else wide,t=i/10) for i in range(21)]
a=old.classify_main_scenes(rows,(1920,1080));b=new.classify_main_scenes(rows,(1920,1080))
res={'description':'Existing base small-wide group endpoints also satisfy the new compact rule after excluding one low-confidence outlying pose. The gate must distinguish added compact support from pre-existing base support.',
 'old_distributed':bool(old.distributed_full_body_ensemble(wide,(1920,1080))),
 'new_allow_compact':bool(new.distributed_full_body_ensemble(wide,(1920,1080),allow_compact=True)),
 'before':[{'t':r.t,'scene':x.scene_kind} for r,x in zip(rows,a)],
 'after':[{'t':r.t,'scene':x.scene_kind} for r,x in zip(rows,b)],
 'old_group_changed_to_main':[r.t for r,x,y in zip(rows,a,b) if x.scene_kind=='group' and y.scene_kind=='main']}
(out/'veto-existing-group-counterexample.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res))
current=json.loads((out/'compact-scene-independent-review.json').read_text())
prior=json.loads((out/'compact-scene-before-veto-fix.json').read_text())
print('Initial counter fixed',not current['veto_bypass_counterexample']['central_interval_changed_to_group'],
      'three videos unchanged',current['actual']==prior['actual'],'fixed source hash',current['proposed_segment_sha256'])
