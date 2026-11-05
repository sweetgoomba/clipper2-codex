"""Retain a verified main through a context-compatible medium ensemble.

This is an output-role refinement. Frozen final names and original joint face
observations are inputs, never modified or promoted to new identity evidence.
"""

from dataclasses import replace
from bisect import bisect_right
import numpy as np

from .observed_main import retained_bodies, strict_pose_corresponding

VERSION = "main_scene_context_v4_bounded_role_retention"


def _foreground_composition(record, role, video_size):
    """Recheck original face/torso prominence, including faceless competitors.

    This supplies role evidence only inside a bounded, independently named
    part. The selected body's torso need not intersect the exact center pixel.
    """
    from .stage_prominence import foreground_subject, selected_foreground_torso
    target = record.candidate_main_bbox
    if (target is None or role.get('reason') not in
            ('corroborated_foreground_subject', 'confirmed_corroborated_foreground_subject')
            or role.get('box') is None
            or not np.allclose(role['box'], target, atol=1e-3, rtol=0)
            or not selected_foreground_torso(record, target, video_size)):
        return False
    features = []
    seen = set()
    for feature in role.get('features', []):
        index = feature.get('index')
        if (not isinstance(index, int) or index in seen
                or not 0 <= index < len(record.person_bboxes)
                or feature.get('box') is None
                or not np.allclose(feature['box'], record.person_bboxes[index], atol=1e-3, rtol=0)
                or feature.get('size') is not None and feature.get('source') not in
                    ('detected', 'repeated_same_pose_geometry')):
            return False
        seen.add(index)
        features.append(dict(feature, pose_keypoints=record.person_pose_keypoints[index]))
    selected = foreground_subject(features, *video_size)
    return bool(selected is not None and selected.get('source') == 'detected'
                and np.allclose(selected['box'], target, atol=1e-3, rtol=0))


def _all_other_model_names_rejected(joint,name):
    """A failed face cannot contradict a frozen body path without a rival.

    Validate both complete original model rankings, including their aggregate,
    before allowing this exception to ordinary weak-distance support. Merely
    being the joint best name is insufficient: every other identity must lie
    outside the existing per-model recognition ceiling in both models.
    """
    if joint.get('status') not in ('insufficient','conflict') or joint.get('best')!=name:
        return False
    models=joint.get('model_candidates')
    if not isinstance(models,list) or len(models)!=2:return False
    tables=[]
    try:
        if any(not np.isfinite(joint[key]) for key in ('primary','secondary','distance','margin')):
            return False
        for rows,key in zip(models,('primary','secondary')):
            table={r['name']:float(r['distance']) for r in rows}
            if (len(table)!=len(rows) or len(table)<2 or name not in table
                    or any(not isinstance(n,str) or not n or not np.isfinite(d) or not 0<=d<=2
                           for n,d in table.items())
                    or abs(table[name]-joint[key])>1e-6):return False
            tables.append(table)
        if tables[0].keys()!=tables[1].keys():return False
        ranked=sorted(((tables[0][n]+tables[1][n])/2,n) for n in tables[0])
        if (ranked[0][1]!=name or abs(ranked[0][0]-joint['distance'])>1e-6
                or abs(ranked[1][0]-ranked[0][0]-joint['margin'])>1e-6):return False
    except (KeyError,TypeError,ValueError):
        return False
    return all(d>.6 for table in tables for n,d in table.items() if n!=name)


def _composition(record, video_size, *, bounded=False):
    width,height=video_size
    boxes=[np.asarray(b) for b in record.person_bboxes]
    poses=[np.asarray(p) for p in record.person_pose_keypoints]
    target=record.candidate_main_bbox
    if (target is None or len(boxes)!=len(poses) or not boxes
            or any(b.shape!=(4,) or not np.isfinite(b).all() for b in boxes)
            or any(p.shape!=(17,3) for p in poses)):
        return False,False
    selected=[i for i,b in enumerate(boxes) if np.allclose(b,target,atol=1e-3,rtol=0)]
    kept=retained_bodies(boxes,poses)
    if len(selected)!=1 or selected[0] not in kept:
        return False,False
    selected=selected[0]
    owners=[];complete=0;selected_extent=None;incomplete=False
    for i in kept:
        box,k=boxes[i],poses[i]
        visible=(np.isfinite(k).all(axis=1)&(k[:,2]>=.5)
            &(k[:,0]>=max(0,box[0]))&(k[:,0]<=min(width-1,box[2]))
            &(k[:,1]>=max(0,box[1]))&(k[:,1]<=min(height-1,box[3])))
        head=visible[:5].sum()>=2
        torso=visible[[5,6,11,12]].all()
        if not head and not (torso and (k[[5,6,11,12],2]>=.75).all()):
            continue
        if not torso:
            incomplete=True
            continue
        xy=k[[5,6,11,12],:2]
        if xy[:,0].min()<=width/2<=xy[:,0].max():
            owners.append(i)
        full=bool(head and visible[[15,16]].all()
            and k[:5,1][visible[:5]].max()<k[[5,6],1].mean()
            <k[[11,12],1].mean()<k[[15,16],1].mean())
        if full:complete+=1
        if i==selected and head:
            if full:
                selected_extent=float(k[[15,16],1].max()-k[:5,1][visible[:5]].min())
    central=(not incomplete and complete>=3 and owners==[selected]
        and selected_extent is not None and (bounded or selected_extent>height/3))
    # Original main eligibility already measured the composition. Requiring a
    # second close-up threshold loses a confirmed part during a medium view.
    return bool(central),bool(record.scene_kind=='main'
        and record.scene_reason=='main_eligible_composition')


def preserve_main_context(records, identity, joint_matches, *, video_size, fps, cut_frames=None,
                          handoffs=(), camera_transitions=(), resolve_transition=None,
                          role_observations=(), camera_episodes=None):
    audit=dict(version=VERSION,reason='complete',changes=[],paths=[])
    if cut_frames is None:
        return records,dict(audit,reason='cut_inventory_unavailable')
    if not records or not identity.get('evidence'):
        return records,audit
    cuts=sorted(set(cut_frames))
    roles={r['frame']:r for r in role_observations}
    # Freeze original group runs before center/context retention consumes a
    # prefix. The remainder is not a new, independently exclusive group run.
    original_group_bounds={}
    i=0
    while i<len(records):
        if records[i].scene_kind!='group':
            i+=1;continue
        start=i
        while i<len(records) and records[i].scene_kind=='group':i+=1
        for j in range(start,i):original_group_bounds[j]=(start,i)
    evidence={}
    for rows in identity['evidence']:
        for row,_ in rows:
            if (row.association=='confirmed' and not row.failure
                    and row.embedding is not None and row.detector_score>=.8):
                evidence.setdefault(row.frame_index,[]).append(row)
    spans=list(zip(identity['segments'],identity['decisions'],strict=True))
    rows=[]
    for record in records:
        frame=round(record.t*fps)
        names={d.reference_id for s,d in spans if s.start<=record.t<s.end and d.status=='matched'}
        name=next(iter(names)) if len(names)==1 else None
        owned=record.candidate_main_bbox is not None and any(
            abs(r.time_seconds-record.t)<1e-6 and np.allclose(
                r.body_bbox,record.candidate_main_bbox,atol=1e-3,rtol=0)
            for r in evidence.get(frame,[]))
        central,clear=_composition(record,video_size)
        joint=joint_matches.get(frame,{})
        direct=joint.get('name') if owned and joint.get('status')=='accepted' else None
        # Only agreeing, noncompetitive weak-distance results may be bounded.
        # Missing results are not equivalent to explicit conflicting results.
        weak=(not joint or (joint.get('status')=='insufficient'
            and joint.get('reason')=='joint_video_rejected' and joint.get('best')==name
            and (joint.get('margin') is None or joint['margin']>=.08)))
        rows.append(dict(frame=frame,time=record.t,name=name,owned=bool(owned),central=central,
            clear=clear,direct=direct,weak=weak,scene=record.scene_kind))
    support={i for i,r in enumerate(rows) if r['name'] and r['direct']==r['name']}
    direct=[i for i,r in enumerate(rows) if r['direct']]
    for left,right in zip(direct,direct[1:]):
        a,b=rows[left],rows[right]
        if a['direct']==b['direct'] and b['time']-a['time']<=.600001:
            support.update(i for i in range(left+1,right) if rows[i]['owned']
                and rows[i]['weak'] and rows[i]['name']==a['direct'])

    def continuous(a,b,name):
        if not 0<abs(a['time']-b['time'])<=.200001:
            return False
        lower,upper=sorted([a['time'],b['time']])
        if any(lower<h['time']<=upper and h['previous_time']<upper for h in handoffs):
            return False
        lo,hi=sorted([a['frame'],b['frame']])
        crossed=sum(lo<c<=hi for c in cuts)
        return crossed==0 or (crossed==1 and a['direct']==b['direct']==name)

    # A weak tail may remain inside an already named part after its last good
    # face. Bound it by original direct support, without chaining weak results
    # into new anchors or carrying a weak face across a camera cut.
    for start in direct:
        seed=rows[start]
        if seed['direct']!=seed['name']:
            continue
        for direction in (-1,1):
            index=start+direction;previous=seed
            while 0<=index<len(rows):
                row=rows[index]
                if (abs(row['time']-seed['time'])>.600001 or not row['owned']
                        or not row['weak'] or row['name']!=seed['name']
                        or not continuous(previous,row,seed['name'])):
                    break
                support.add(index)
                previous=row;index+=direction

    # Freeze eligible original foreground runs before applying any changes.
    seeds=[];i=0
    while i<len(rows):
        start=i;r=rows[i];i+=1
        if not r['clear'] or start not in support:continue
        while (i<len(rows) and rows[i]['clear'] and i in support
                and rows[i]['name']==r['name'] and continuous(rows[i-1],rows[i],r['name'])):
            i+=1
        if rows[i-1]['time']-r['time']>=.15-1e-6:
            seeds.extend([start,i-1])
    changed={}
    exclusive_foreground=set()
    for start in sorted(set(seeds)):
        seed=rows[start]
        for direction in (-1,1):
            previous=seed;index=start+direction;path=[];groups=[]
            while 0<=index<len(rows):
                row=rows[index];record=records[index]
                if (not continuous(previous,row,seed['name']) or index not in support
                        or row['name']!=seed['name'] or not row['central']
                        or row['scene'] not in ('main','group')
                        or row['scene']=='group' and record.scene_reason not in ('distributed_full_body_ensemble','continuous_distributed_ensemble')):
                    break
                path.append(index)
                if row['scene']=='group':groups.append(index)
                previous=row;index+=direction
            if groups and abs(rows[path[-1]]['time']-rows[path[0]]['time'])>=.15-1e-6:
                for index in groups:changed.setdefault(index,start)
                audit['paths'].append(dict(seed_frame=seed['frame'],name=seed['name'],
                    frames=[rows[j]['frame'] for j in path],
                    direct_frames=[rows[j]['frame'] for j in path if rows[j]['direct']==seed['name']]))

    # A small view can sit between two independently confirmed views of the
    # same ongoing main. Require an entire observed body path and both frozen
    # face endpoints; a distant ensemble alone cannot seed this retention.
    eligible={i for i,row in enumerate(rows) if row['scene']=='main'}|set(changed)
    transitions={item['frame']:item for item in camera_transitions}
    def body(record):
        boxes=[np.asarray(b) for b in record.person_bboxes]
        poses=[np.asarray(p) for p in record.person_pose_keypoints]
        features=[dict(index=i,pose_keypoints=poses[i]) for i in retained_bodies(boxes,poses)]
        selected=[f for f in features if np.allclose(boxes[f['index']],record.candidate_main_bbox,atol=1e-3,rtol=0)]
        return dict(features=features),selected[0] if len(selected)==1 else None
    i=0
    while i<len(rows):
        if i in eligible:
            i+=1;continue
        start=i
        while i<len(rows) and i not in eligible:i+=1
        if start==0 or i==len(rows):continue
        end=i;name=rows[start-1]['name'];left=start-1;right=end
        while left in eligible and rows[left]['name']==name and rows[left]['direct']!=name:left-=1
        while right in eligible and rows[right]['name']==name and rows[right]['direct']!=name:right+=1
        if (left<0 or right>=len(rows) or left not in eligible or right not in eligible
                or not name or rows[left]['direct']!=name or rows[right]['direct']!=name
                or rows[right]['time']-rows[left]['time']<.15):continue
        if any(rows[left]['time']<h['time']<=rows[right]['time'] for h in handoffs):continue
        foreground={j for j in range(start,end)
                    if _foreground_composition(records[j],roles.get(rows[j]['frame'],{}),video_size)}
        # A single instantaneous prominence estimate cannot retain a part.
        # Never promote these observations into face or future role anchors.
        sustained_foreground=(len(foreground)>=2 and
            rows[max(foreground)]['time']-rows[min(foreground)]['time']>=.15-1e-6)
        if any(rows[j]['scene']!='group' or records[j].scene_reason not in ('distributed_full_body_ensemble','continuous_distributed_ensemble')
               or not (_composition(records[j],video_size,bounded=True)[0]
                       or sustained_foreground and j in foreground) for j in range(start,end)):continue
        if any(row['name']!=name or row['direct'] not in (None,name)
               for row in rows[left:right+1]):continue
        # The original named main can contain weak or missing face samples.
        # Only newly included group samples need fresh eligibility support.
        if any(not row['owned'] or
               row['direct'] is None and not (row['weak'] or
                   _all_other_model_names_rejected(joint_matches.get(row['frame'],{}),name)) or
               joint_matches.get(row['frame'],{}).get('best',row['direct'])!=name
               for row in rows[start:end]):continue
        crossed=[cut for cut in cuts if rows[left]['frame']<cut<=rows[right]['frame']]
        if any(cut not in transitions for cut in crossed):continue
        for cut in crossed:
            if transitions[cut].get('structure_deferred') and resolve_transition is not None:
                transitions[cut].update(resolve_transition(cut))
                transitions[cut].pop('structure_deferred',None)
        physical=[cut for cut in crossed if transitions[cut].get('structure',{}).get('continuous') is not True]
        if len(physical)>1:continue
        # Both endpoints are original owned, accepted same-name faces. With
        # one cut they independently establish that name in each shot; pose
        # continuity is still required on every observed step within a shot.
        if physical and not rows[left]['frame']<physical[0]<=rows[right]['frame']:continue
        direct_support=[row for row in rows[left:right+1] if row['direct']==name]
        # Bound each new sample by original face support in its own shot.
        # Two independently recognized shots need not share a global duration
        # cap, and an intervening run of direct faces does not become a gap.
        if any(not any(bisect_right(physical,r['frame'])==bisect_right(physical,row['frame'])
                       and abs(r['time']-row['time'])<=.600001 for r in direct_support)
               for row in rows[start:end]):continue
        linked=True
        for j in range(start,end+1):
            a,b=rows[j-1],rows[j]
            if not 0<b['time']-a['time']<=.200001:
                linked=False;break
            if any(a['frame']<cut<=b['frame'] for cut in physical):continue
            old,selected=body(records[j-1]);new,target=body(records[j])
            found=strict_pose_corresponding(old,selected,new) if selected is not None else None
            if found is None or target is None or found['index']!=target['index']:
                linked=False;break
        if linked:
            for j in range(start,end):changed.setdefault(j,left)
            # Drop the redundant group export only when the whole original
            # group run has a uniquely corroborated front performer. Ordinary
            # center/context retention keeps its existing dual eligibility.
            group_start,group_end=original_group_bounds[start]
            original_run=range(group_start,group_end)
            if (sustained_foreground and all(j in changed and rows[j]['name']==name
                    and _foreground_composition(records[j],roles.get(rows[j]['frame'],{}),video_size)
                    for j in original_run)):
                exclusive_foreground.update(original_run)
            audit['paths'].append(dict(seed_frame=rows[left]['frame'],name=name,
                frames=[rows[j]['frame'] for j in range(start,end)],
                direct_frames=[rows[left]['frame'],rows[right]['frame']],reason='bounded_same_main_body_path',
                foreground_frames=[rows[j]['frame'] for j in sorted(foreground)] if sustained_foreground else []))
    # A separate retention proof reads only frozen inputs. It runs after all
    # existing context passes so newly retained rows cannot seed another gap.
    from .role_state import prove_role_state
    original_names={row['frame']:row['name'] for row in rows
                    if row['name'] and row['owned'] and row['direct']==row['name']}
    role_state=prove_role_state(records,role_observations,original_names,
        video_size=video_size,fps=fps,cut_frames=cuts,handoffs=handoffs,
        camera_episodes=camera_episodes,
        identity_boundaries=[s.start for s,_ in spans]+[s.end for s,_ in spans])
    audit['role_state']=role_state
    retained_role_frames=set()
    frame_indices={row['frame']:i for i,row in enumerate(rows)}
    for part in role_state['accepted']:
        seed=frame_indices[part['proof_frames'][0]]
        for frame in part['main_role_frames']:
            index=frame_indices[frame]
            if index not in changed:
                changed[index]=seed
                retained_role_frames.add(frame)
        # This proof retains a member part; it does not disprove the ensemble.
        exclusive_foreground.difference_update(frame_indices[f] for f in part['main_role_frames'])
    result=list(records)
    for index,start in sorted(changed.items()):
        record=records[index]
        result[index]=replace(record,main_id=record.candidate_main_id,
            main_bbox=record.candidate_main_bbox,scene_kind='main',scene_reason='verified_main_context',
            is_group=False if index in exclusive_foreground else record.is_group)
        audit['changes'].append(dict(frame=rows[index]['frame'],time=record.t,
            name=rows[index]['name'],seed_frame=rows[start]['frame'],before='group',after='main',
            exclusive_foreground=index in exclusive_foreground,
            role_retention=rows[index]['frame'] in retained_role_frames))
    return result,audit
