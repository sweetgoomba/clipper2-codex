"""Keep a measured ensemble through a scale threshold in the same shot.

Uses existing pose observations only. Names and clip lengths are not inputs.
A failed ensemble test does not establish a solo; continuation requires its own
complete formation, correspondence and original role evidence at every sample.
"""
from dataclasses import replace
import math
import numpy as np

from .segment import _observed_body_joints, bbox_iou
from .observed_main import retained_bodies, strict_pose_corresponding
from .native_scene import _distinct_complete_count


def _formation(record, size):
    width, height = size
    boxes, poses = record.person_bboxes, record.person_pose_keypoints
    if len(boxes) != len(poses) or len(boxes) < 3:
        return None
    if any(np.asarray(p).shape != (17,3) or not np.isfinite(p).all() for p in poses):
        return None
    people=[]
    for i in retained_bodies(boxes, poses):
        box,pose=np.asarray(boxes[i]),np.asarray(poses[i])
        if (box.shape!=(4,) or not np.isfinite(box).all() or (box[2:]<=box[:2]).any()
                or (box[:2]<=0).any() or (box[2:]>=np.array([width,height])).any()):
            return None
        visible,inside,head,torso,reliable=_observed_body_joints(box,pose,size)
        if (not head or not reliable or not (visible[[15,16]] & inside[[15,16]]).all()
                or not pose[:5,1][visible[:5]&inside[:5]].max() < pose[[5,6],1].mean()
                < pose[[11,12],1].mean() < pose[[15,16],1].mean()):
            return None
        xy=pose[[5,6,11,12],:2]
        people.append(dict(index=i,box=box,pose_keypoints=pose,full=True,
                           rect=np.r_[xy.min(axis=0),xy.max(axis=0)]))
    if len(people)<3 or _distinct_complete_count(people)!=len(people):
        return None
    heights=[p['box'][3]-p['box'][1] for p in people]
    if max(heights)>2*height/3 or max(heights)>1.4*np.median(heights):
        return None
    return dict(features=people)


def _same_formation(before,after):
    left,right=before['features'],after['features']
    if len(left)!=len(right):
        return False
    matrix=np.array([[bbox_iou(a['box'],b['box']) for b in right] for a in left])
    assigned=[];pose_pairs=0
    for i,a in enumerate(left):
        ranked=np.argsort(matrix[i])[::-1];j=int(ranked[0])
        column=np.sort(matrix[:,j])[::-1]
        if (matrix[i,j]<.3 or matrix[i,j]-matrix[i,ranked[1]]<.08
                or int(np.argmax(matrix[:,j]))!=i or column[0]-column[1]<.08):
            return False
        ratio=(right[j]['box'][3]-right[j]['box'][1])/(a['box'][3]-a['box'][1])
        if not 1/1.4<=ratio<=1.4:
            return False
        matched=strict_pose_corresponding(before,a,after)
        if matched is not None and matched['index']==right[j]['index']:
            pose_pairs+=1
        elif matched is not None:
            return False
        assigned.append(j)
    return len(set(assigned))==len(left) and pose_pairs>=3


def _role_remains_ensemble(record, role, formation, size):
    from .stage_prominence import foreground_subject
    if (role is None or role.get('box') is None or record.candidate_main_bbox is None
            or not np.allclose(role['box'],record.candidate_main_bbox,atol=1e-3,rtol=0)):
        return False
    people={p['index']:p for p in formation['features']};features=[]
    for f in role.get('features',[]):
        i=f.get('index')
        if (i not in people or f.get('box') is None
                or not np.allclose(f['box'],people[i]['box'],atol=1e-3,rtol=0)):
            return False
        if f.get('size') is not None and (f.get('source') not in
                ('detected','repeated_same_pose_geometry') or not np.isfinite(f['size'])
                or f['size']<=0 or f.get('x') is None or not np.isfinite(f['x'])):
            return False
        features.append(dict(f,pose_keypoints=people[i]['pose_keypoints']))
    if len(features)!=len(people) or len({f['index'] for f in features})!=len(people):
        return False
    measured=sorted((f for f in features if f.get('size') is not None),key=lambda f:f['size'],reverse=True)
    if (len(measured)>=2 and measured[0]['size']>=1.3*measured[1]['size']
            and .25*size[0]<=measured[0]['x']<=.75*size[0]):
        return False
    return foreground_subject(features,*size) is None


def continue_observed_ensemble(records, *, video_size, fps, sample_step,
                                cut_frames, handoffs, camera_episodes, role_observations):
    audit=dict(version='observed_ensemble_scale_continuity_v1',continued_frames=[],candidates=[])
    if any(x is None for x in (cut_frames,handoffs,camera_episodes,role_observations)):
        return records,dict(audit,reason='missing_original_proofs')
    if not math.isfinite(fps) or fps<=0 or sample_step<1:
        return records,dict(audit,reason='invalid_source_cadence')
    frames=[round(r.t*fps) for r in records];cuts=sorted(set(cut_frames))
    roles={r['frame']:r for r in role_observations};output=list(records)
    i=1
    while i<len(records):
        if not (records[i-1].scene_kind=='group' and records[i-1].scene_reason=='distributed_full_body_ensemble'
                and records[i].scene_kind=='main'):
            i+=1;continue
        start=i;end=i
        next_cut=next((c for c in cuts if c>frames[start-1]),None)
        if next_cut is None:
            i+=1;continue
        while end<len(records) and frames[end]<next_cut:
            end+=1
        item=dict(first_frame=frames[start],cut_frame=next_cut,frames=frames[start:end])
        audit['candidates'].append(item);i=max(start+1,end)
        anchor=start-1
        while (anchor>0 and records[anchor-1].scene_kind=='group'
                and records[anchor-1].scene_reason=='distributed_full_body_ensemble'
                and frames[anchor]-frames[anchor-1]==sample_step
                and not any(frames[anchor-1]<c<=frames[anchor] for c in cuts)):
            anchor-=1
        if (end==start or end>=len(records) or frames[end]-frames[end-1]!=sample_step
                or records[start-1].t-records[anchor].t<.15-1e-6
                or any(frames[j]-frames[j-1]!=sample_step for j in range(start,end))
                or any(r.scene_kind!='main' or r.scene_reason!='main_eligible_composition'
                       for r in records[start:end])):
            item['reason']='missing_stable_ensemble_or_shot_boundary';continue
        if (any(records[start-1].t<h['time']<records[end].t for h in handoffs)
                or any(p['start_frame']<=frames[end-1] and p['end_frame']>=frames[start-1]
                       for p in camera_episodes)):
            item['reason']='new_original_role_evidence';continue
        local=[_formation(r,video_size) for r in records[start-1:end]]
        if any(p is None for p in local) or not all(_same_formation(a,b) for a,b in zip(local,local[1:])):
            item['reason']='unconfirmed_complete_formation';continue
        if any(roles.get(frames[j],{}).get('reason') not in
               ('measured_face_composition','confirmed_measured_face_composition',
                'near_tie_keep_incumbent','awaiting_sustained_composition','confirmed_near_tie_transition')
               for j in range(start,end)):
            item['reason']='different_or_missing_role_basis';continue
        if not all(_role_remains_ensemble(records[j],roles.get(frames[j]),local[j-start+1],video_size)
                   for j in range(start,end)):
            item['reason']='new_or_unconfirmed_foreground_measurement';continue
        for j in range(start,end):
            output[j]=replace(records[j],main_id=None,main_bbox=None,is_group=True,
                group_bboxes=list(records[j].person_bboxes),scene_kind='group',
                scene_reason='continuous_distributed_ensemble')
        audit['continued_frames'].extend(frames[start:end]);item['reason']='same_observed_ensemble_until_source_cut'
    return (output if audit['continued_frames'] else records),dict(audit,reason='complete')
