"""Reviewed front-of-formation subjects must survive a center-line bias."""
import json
from pathlib import Path
import numpy as np
import pytest
from dance_highlight.services.main_role_timeline import choose_roles


DATA = json.loads((Path(__file__).parent / 'fixtures/dance_foreground_reviewed.json').read_text())


@pytest.mark.parametrize('case', DATA['cases'], ids=lambda c: str(c['time']))
def test_reviewed_front_performer_is_not_replaced_by_back_row_center(case):
    row = dict(case, features=[dict(f, pose_keypoints=np.array(f['pose_keypoints'])) for f in case['features']])
    old = {row['frame']: {'candidate_main_bbox': row['features'][0]['box']}}
    choose_roles([row], old, DATA['width'], DATA['height'], [], lambda *_: None)
    assert row['index'] == case['expected']


def test_invalid_pose_cannot_supply_foreground_override():
    from dance_highlight.services.stage_prominence import foreground_subject
    row = DATA['cases'][0]
    features = [dict(f, pose_keypoints=np.array(f['pose_keypoints'])) for f in row['features']]
    features[-1]['pose_keypoints'][11:13, 2] = 0
    assert foreground_subject(features, DATA['width'], DATA['height']) is None


def test_two_equally_prominent_foreground_people_are_not_a_solo_subject():
    from dance_highlight.services.stage_prominence import foreground_subject
    row = DATA['cases'][0]
    features = [dict(f, pose_keypoints=np.array(f['pose_keypoints'])) for f in row['features']]
    features.append(dict(features[-1], index=20, x=DATA['width'] - features[-1]['x']))
    assert foreground_subject(features, DATA['width'], DATA['height']) is None


def test_center_handoff_cannot_backdate_over_confirmed_front_performer():
    from dance_highlight.services.main_role_timeline import extend_near_ties
    rows=[]
    for frame in range(7):
        features=[]
        for index,(x,size,length) in enumerate([(65,11,22),(50,10,20),(25,8,18)]):
            if index==0 and frame>=3:size,length=9,19
            pose=np.ones((17,3));pose[:,:2]=[x,20]
            pose[[5,11],0]-=5;pose[[6,12],0]+=5
            pose[[11,12],1]+=length
            features.append(dict(index=index,x=x,size=size,box=[x-5,0,x+5,90],
                                 source='detected',pose_keypoints=pose))
        rows.append(dict(frame=frame,time=frame/10,features=features))
    def corresponding(row,person,other):return other['features'][person['index']]
    old={r['frame']:dict(candidate_main_bbox=r['features'][0]['box']) for r in rows}
    choose_roles(rows,old,100,100,[],corresponding)
    assert [r['index'] for r in rows]==[0,0,0,1,1,1,1]
    extend_near_ties(rows,[],corresponding)
    assert [r['index'] for r in rows]==[0,0,0,1,1,1,1]


def test_faceless_front_row_peer_prevents_a_false_solo_override():
    from dance_highlight.services.stage_prominence import foreground_subject
    case = DATA['cases'][0]
    features = [dict(f, pose_keypoints=np.array(f['pose_keypoints'])) for f in case['features']]
    candidate = foreground_subject(features, DATA['width'], DATA['height'])
    assert candidate is not None
    features.append(dict(candidate, index=99, size=None, source='missing',
                         pose_keypoints=candidate['pose_keypoints'].copy()))
    assert foreground_subject(features, DATA['width'], DATA['height']) is None


def test_reviewed_mmn_center_subject_survives_two_kneeling_front_performers():
    from dance_highlight.services.observed_main import strict_pose_corresponding
    data = json.loads((Path(__file__).parent / 'fixtures/dance_scene_review/mmn103_role_subject.json').read_text())
    rows = data['rows']
    for row in rows:
        for feature in row['features']:
            feature['pose_keypoints'] = np.array(feature['pose_keypoints'])
    old = {r['frame']:dict(candidate_main_bbox=r['original_box']) for r in rows}
    choose_roles(rows, old, data['width'], data['height'], data['cuts'], strict_pose_corresponding)
    assert all(r['box'] == r['expected_box'] for r in rows)
