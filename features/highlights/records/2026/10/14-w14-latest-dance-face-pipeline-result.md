# W14 — 최신 안무27 출력과 얼굴 매칭 연결 (2026-10-14)

## 결론

사용자 계속 진행 지시에 따라 최신 W13 저장 출력의 메인 몸→얼굴→등록 멤버 매칭 평가를 연결했다. 기존 YuNet + SFace를 유지했다. **정확도 개선 성공은 아니다.** 같은42메인 범위에서 개별 합의12개→시간 결합안18개 배정이나,추가6개에는 연결 identity GT가 없다. GT부분14범위는 양쪽7일치/7보류로 동일하고,혜인GT10개가 있는3범위도 모두보류다. 결합안 제품채택 없음.

[멤버 카드→구간→선택얼굴/메인몸/원본재생](http://127.0.0.1:58261/latest-dance-faces-v1/index.html). 첫 화면은 구간51 혜인미매칭. `혜인0`은 이 시험의 확정배정0이라는 뜻이다. 새 사용자 정답입력/내보내기는 요구하지 않는다.

## 동결 입력·실행

Worktree `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013`, repo `desktop/clipper_python`, branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e` + 개별파일hash로 고정한 평가코드.

출력은 위 worktree의 `evaluation-output/candidate-comparison-20261014/latest-dance-pipeline-v1/`. 실행전 manifest SHA256 `84840f8ce2e461a25cc575af230e748837a4c81b48b2248099ec6a505ef912d5`.

이전 W14 20구간/406얼굴은 옛 MoveNet 메인 입력이었다. 현재 W13의 RTMDet-nano/RTMPose-m iteration27 combined와 혼동하지 않는다. 최신 W13 `role-continuity-27/revision-a/combined-frames.json`, `combined-segments.json`, `manifest-frozen.json`, `receipt.json`과 `handoff-26/revision-b/recent_bridge-pose.json`을 읽기전용으로 고정했다. 실제 절대경로/hash47개는 manifest에 있다. W13 latest개발본은 정답/제품채택본이 아니다.

70구간(single40/joint1/group7/unknown22)→segment×main42범위. 공동메인2개는별도scope,군무/unknown은매칭하지않음. 같은track숫자가다른구간에나와도합치지않음. 실제shot cut/동일인track 보증없음. 옛406얼굴을 현재머리와 대조하면 joint추가로407비교:같은얼굴100/group212/unknown16/머리에서없음71/머리불확실3/다른후보3/공유머리2. 모집단변화라 개선율로 해석금지.

- source yFTAYXDTjqI/source.mp4:1920×1012,60000/1001fps,133.654059초; SHA256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`
- YuNet `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`
- SFace `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`
- 사용자 기존GT `684cbd4d1a40904e64b43b9b9efeeaad52a94e7dafebee1a7ecfd2f4399b2aec`
- 각scope 실제 첫/중간/끝 + 기존답변 frame index;이름/점수로선택하지않음. 158고유프레임/161main표본. frame index와W13 derived_seconds이며 실제PTS보장아님. 기존영상은개발자료,무작위평가아님.
- full1920×1012 YuNet(score.6/NMS.3/topK5000)→모든얼굴→선택자세머리 연결→SFace alignCrop112BGR/128차원L2. 참조23은같은모델/정렬/런타임재현된캐시. 최고점수얼굴로대체하지않고,같은시점동일얼굴이공동메인둘에연결되면둘다보류.
- Apple M4/macOS27arm64/Python3.11.12/OpenCV4.13.0/CPU1thread/batch1.
- 상한250검출/300인식,300초/4GiB/300MiB,외부ps250ms감시. 실제158검출/129인식,worker26.366초/supervisor26.762초,peak525058048bytes(500.7MiB),정상종료.
- 새참조/자세/다른모델추론0,다운로드/설치/API/제품/core/W13수정/커밋/푸시0.

## 동일 입력 두 방식

고정된 기존개발 SFace정책 distance≤.7239670157432556,1·2위차이≥.13533276319503784,최소지지2.

개별합의는 서로다른확정멤버충돌을보존한다. 결합안은 기존확정유지,불충분/거리거부일때만 최소2고유프레임·0.25초이상·모든최근접멤버일치·강한충돌없음 조건으로 평균후L2특징을같은정책과비교한다. **평균특징용별도보정은아니며실험가설이다.** 새영상holdout조정없음. 옛앱20구간과직접전후정확도비교금지.

129임베딩성공/메인머리얼굴없음18/공유머리연결보류11/머리불확실3. 정렬·추론오류0. 실패32개도모두보존.

## 정답 범위와 진단

같은frame+원본좌표IoU≥.5의유일대응만과거답변연결. 35링크중identity미기입1,알려진멤버34(민지11/혜인10/해린6/하니7),다니엘/등록외GT0. **새crop사용자확인/전체scope정답이아니다.** 구간전체에GT전파없음.

|항목|개별합의|시간결합|
|---|---:|---:|
|배정/42범위|12|18|
|부분GT14범위 답변일치|7|7|
|부분GT14범위 보류|7|7|
|부분GT14범위 답변불일치|0|0|

34얼굴개별판정은9정답/25보류/0오배정. 단순점수1위는민지10/11,혜인7/10,해린5/6,하니6/7. 혜인3얼굴은하니를더가깝게보고,혜인1위7얼굴도고정차이기준을넘지못함. 기준만낮추면오배정도늘수있다. 모든후보거리는`recognition-diagnosis.json`.

추가6배정:s0009/1민지,s0034/40다니엘,s0044/71하니,s0046/71해린,s0050/69민지,s0059/139민지. 알려진GT가없으므로정답증가로세지않음.

## 검증·리뷰

새경계/공동메인/중복/시간/충돌/약한근거/공간GT링크/동시얼굴중복 RED→GREEN. 관련평가+공통core111passed. 입력47hash불변,원본crop129픽셀일치,690거리독립계산최대차이8.94e-8,42최종후보정책별도검산.

독립리뷰는샘플링/소유권/GT링크/모델공간/실제42판정도재현했다. 검산코드가후보수락의일부gate를빠뜨린P2한건발견. 3회귀테스트(1표본/작은평균차이/짧은시간·중복)RED→GREEN과111suite/전체검산재통과. 추론결과변경/재추론없음. 남은리뷰지적없음.

UI 실제1920×1012원본재생/끝자동정지/멤버filter/혜인0빈상태·재생비활성/전체복귀/얼굴시점선택확인. 재생중고정박스숨김. HTML timeupdate미리보기끝에는약0.15초지연관찰;frame정확export구현아님. `review-screen.png` 저장.

## 소유권·남은 작업

W14평가adapter/리포트/계획/인계만추가. public core,W13 main/mapping/crop/adapter,기존제품/GT/venv/lock/이전실험보존. 최신W13 **저장출력의평가연결은완료**,제품adapter통합/새영상W13출력/동일인track/전체품질/Windows배포는미검증.

병합순서:W14공개계약/fixture→W13동일인scope·실패compatibility→W13adapter/선택venv검증→제품통합. 이번결합안은미채택. 남은핵심은혜인/하니점수분리력,신규6배정의독립정답·소유권검증,짧은구간/실제shot/trackscope계약이다. 사용자전체정답표재작성요구없음. 후속실험도개발자료회귀를함께확인하며새영상은조정에쓰지않는다.
