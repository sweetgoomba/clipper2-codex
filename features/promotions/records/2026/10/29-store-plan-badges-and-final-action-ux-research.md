# 앱 스토어의 요금제 표시와 최종 실행 제한 UX 사례 조사

기준일: **2026-10-29 KST**. 공식 자료로 17개 서비스를 조사했다. 사용자 최신 방향과 UI 제안을 구분한다. 제품 코드·서버·DB를 수정하거나 외부 서비스의 설치·구매·체험을 실행하지 않았다. UI 시안/문구는 아직 선택한 최종 디자인이 아니다.

## 1. 최신 사용자 방향과 이전 설계의 보정

전략실·기획팀 등의 공통 의견으로 사용자가 전달한 방향:

- 현재 요금제에서 미제공하는 플러그인도 스토어에 보인다.
- 설치·상세 보기·기능 화면 진입·편집 준비는 허용한다.
- 해당 기능의 최종 생성 등 실제 유료 동작에서 현재 요금제와 크레딧을 검사하고 필요한 경우 업그레이드를 안내한다.
- 예시의 하이라이트 Pro 이상은 설명용이다. 실제 허용 목록은 회사 설정으로 정한다.

이전 W19 기록의 ‘진입/실행 제한’은 **요금제 미제공이라는 이유만으로 설치·화면 진입부터 차단하지 않는 방향**으로 보정한다. 최종 동작의 서버 검사는 유지하되 각 플러그인에서 어느 동작이 최종 유료 실행인지 정의해야 한다. 전체 긴급 비활성화는 요금제 제한과 다른 W18 후속이다.

새 메시지는 노출·설치 정책의 방향을 구체화했으며 카드·모달 디자인에 대한 이사님의 최종 디자인 승인을 받았다는 증거는 아니다.

## 2. 현재 클리퍼 화면에서 재사용할 부분

- `src/shell/store/plugin-card/plugin-card.component.html`: 카드 본체 선택이 상세를 열고 즐겨찾기와 설치/바로가기 행동은 형제 버튼이다.
- `plugin-detail/plugin-detail.component.html`: 상단 이름/소개와 설치 칩, 본문 단계 설명·설치 정보, 하단 설치/바로가기/제거를 제공한다.
- `store/store.component.html`: 이름/상황 검색·분류 칩·카드 목록·설명 모달과 모두 설치 버튼이 있다.
- 기존 Material 카드/칩/대화상자·시맨틱 토큰을 재사용할 수 있다. 요금제 배지를 추가하며 즐겨찾기·설치 상태·요금제 조건을 같은 상태로 합치지 않는다.

경로는 준비한 worktree의 `desktop/clipper_angular` 기준이며 실제 실행 앱의 현재 화면을 새로 캡처한 것은 아니다.

## 3. 추천 UX

### 카드

- 카드의 밝기·설명·클릭·설치/바로가기는 유지하고 제목 부근에 작은 **Pro 이상** 또는 **Business** 배지를 제안한다.
- 카드 전체 흐림/비활성 커서는 설치·탐색도 불가능한 기능처럼 읽히므로 이 방향에는 추천하지 않는다.
- 유료 등급의 상위 포함 관계가 있으므로 카드에는 최소 요금제를 짧게, 상세에는 Pro·Business 등 전체 적용 목록을 표시하는 편이 간결하다. 기본 상태의 독립 허용 관계가 예외인 경우에는 실제 허용 목록에서 안전하게 문구를 계산한다.
- 현재 Basic 회원에게 필요하면 ‘결과 생성 시 업그레이드 필요’ 같은 짧은 설명을 보조한다. 모든 카드를 과도한 업그레이드 배너로 바꾸지 않는다.
- 설치됨과 요금제 조건은 별개로 표시한다. 설치 완료가 실행 권한 획득을 뜻하지 않는다.

### 상세 모달과 설치

설명 아래에 ‘이용 요금제: Pro, Business’, ‘현재 요금제: Basic’, ‘설치·편집은 가능하며 최종 생성에는 Pro 이상 필요’ 같은 안내 영역을 제안한다. 주 버튼은 기존 설치/바로가기를 유지하고 요금제 보기는 보조 링크로 제공한다.

카드를 눌렀다는 이유만으로 업그레이드 모달을 먼저 띄우거나 설치 버튼을 업그레이드 버튼으로 교체하는 것은 이번 방향과 맞지 않는다. 모델 용량이 큰 기능은 기존 설치 동의 안에 최종 실행 조건을 짧게 알리는 정도를 검토한다.

### 편집 준비와 최종 버튼

- 기능 화면에도 비차단 안내를 유지한다. 최종 버튼까지 다 준비한 후 처음 제한 사실을 알리는 흐름은 피한다.
- 실제 생성/추출 등 확정 동작을 누르면 서버가 최신 등급을 확인하고 부족할 때 업그레이드 대화상자를 표시한다. 단순 UI 필터만으로 검사하지 않는다.
- 대화상자는 현재 등급·필요 등급·막힌 동작을 보여주고 ‘계속 편집’과 ‘요금제 보기’ 같은 선택을 제공하는 안이다.
- 입력·편집 상태 보존과 업그레이드 후 복귀·권한 재조회가 필요하다. 복귀만으로 유료 작업을 자동 재실행/청구하지 않는다.
- 등급과 잔액이 모두 부족하면 등급 문제를 먼저 안내하는 안이다. 크레딧을 추가 구매해도 그 기능이 열리지 않는 상태를 잔액 부족만으로 안내하지 않는다.

일부 AI 플러그인은 중간 단계에서도 별도 유료 생성 작업이 있다. 이번 요청을 ‘모든 중간 연산 무료’라고 해석하지 않는다. 그런 작업은 기존 비용을 해당 작업 전 표시하고, 최종 결과의 요금제 제한도 사전에 안내해야 한다. 각 작업의 허용/과금 경계는 실제 기능별로 확인할 기술·정책 항목이다.

## 4. 가까운 정책 사례

| 서비스 | 공식 근거에서 확인한 내용 | 클리퍼에 참고할 점과 차이 |
|---|---|---|
| Adobe Express | 무료 사용자가 Premium 콘텐츠를 문서에서 실험할 수 있고 다운로드·공유 시 업그레이드를 요구 | 준비/미리보기와 결과 이용을 분리. 모든 Premium 기능을 무료 실행한다는 뜻은 아님 |
| Clipchamp | Premium 기능이 들어간 무료 프로젝트의 Export 옵션에 diamond 표시, 제거 또는 업그레이드 후 내보내기 | 편집 허용·내보내기 제한. 플러그인 설치 예시는 아님 |
| Zapier | 디렉터리 Premium 태그, premium 앱/다단계 Zap의 게시 시 Pro 업그레이드 대화상자 | 목록에서 먼저 안내하고 최종 게시에서 검사 |
| Wix Stores | 앱을 무료로 추가·설정하되 고객 주문을 받기 전에 결제 수용 가능한 사이트 플랜 필요 | 앱 설치·설정과 호스트 플랜의 핵심 실행 권한을 분리 |
| Canva | 공식 앱 가이드에 무료/유료 항목 혼합, crown/Pro/tooltip 예시. Premium Apps는 유료 기능 클릭 시 즉시 업그레이드 | 배지·동일 UI 참고. Premium 요소 미리보기와 Premium Apps 즉시 제한을 동일 정책으로 일반화하지 않음 |
| CapCut | Desktop 효과 카드 Pro, 편집 중 Pro 안내, 특정 Export 설정에서 업그레이드 | Desktop 사례 참고. Web은 Apply/Use 시, Mobile은 적용 전 제한 등 플랫폼별 차이가 있음 |
| Figma Community | In-app purchases·사용량/기간 체험 후 파일 내 Buy/Subscribe, 일부 플러그인의 유료 출력 설명 | 열기/편집과 유료 출력의 구분. Figma 요금제 포함이 아닌 독립 앱 구매 |

## 5. 추가 UI와 실행·비용 사례

| 서비스 | 확인 내용 | 주의할 구분 |
|---|---|---|
| VEED | 스크립트·프로젝트 준비와 Generate Video 크레딧을 구분. 모델/길이 선택 후 생성 전 비용 표시 | 요금제 불가 카드보다 실행 전 비용 안내 참고 |
| Descript | Free 출력의 해상도·워터마크 제한, AI 모델별 크레딧 비용 표현 | 전체 실행 불가가 아닌 출력 조건 제한 |
| DaVinci Resolve | 공식 Resolve 20 Guide p.121: Studio Open FX 미리보기/적용 가능, 무료 버전 경고·뷰어 워터마크 | 특정 버전 안내. 최신 전체 동작이나 최종 렌더 hard block을 주장하지 않음 |
| Raycast | 스토어 검색/분류 → 상세 명령/스크린샷 → 설치. Extension Models 문서에 Pro Exclusive | 일반 확장 전체가 유료라는 뜻이 아님 |
| Miro | Included with Miro plans와 Free and paid plans 등을 별도 구분, Connect와 가격 조건 병치 | 호스트 플랜 포함과 앱 별도 구매를 구분 |
| JetBrains Marketplace | Free/Freemium/Free trial, Get와 Pricing의 체험/구매 구분 | IDE 플랜 포함이 아닌 독립 플러그인 라이선스 |
| Atlassian Marketplace | Try it free·가격 탭·사용자 수에 따른 가격/CTA | Jira 등급과 별도 앱 구독 |
| Shopify App Store | 무료 플랜/체험 안내와 설치 CTA를 함께 표시, 하단 플랜 비교 | 앱 별도 과금 |
| Framer Marketplace | Free/Paid 필터, 유료 목록에서도 Open·상세 Open Plugin | 실제 내부 결제 게이트는 실행하지 않음 |
| monday Marketplace | Sign in to install, 설치 앱에서 See plans/Update plan | 앱별 구독이며 외부 청구 앱도 있음 |

## 6. 공식 화면과 출처

### 시각 자료

- [Canva 공식 디자인 가이드 도해](https://www.canva.dev/_next/static/media/02-content-limited-apps.80dfb5c7.png): 무료와 crown 유료 항목의 혼합 목록. 실제 Clipper 시안이나 운영 계정 캡처가 아니다.
- [CapCut 공식 Desktop 화면](https://p16-seeyou-useast5.capcutcdn-us.com/tos-useast5-i-2zwwjm3azk-tx/664b80465ece4737b2659a54baabc592~tplv-2zwwjm3azk-compress%3Aq75.image): 카드·설정의 Pro 표시.
- [Zapier 공식 게시 업그레이드 화면](https://help.zapier.com/hc/article_attachments/35201203526925).
- [Figma 공식 체험 후 구매 안내 이미지](https://help.figma.com/hc/article_attachments/29908421047831).

### 정책과 화면을 확인할 공식 페이지

1. Adobe Express: [Premium 콘텐츠·출력 지침](https://developer.adobe.com/express/add-ons/docs/guides/build/distribute/guidelines/monetization), [Premium 콘텐츠 처리](https://developer.adobe.com/express/add-ons/docs/guides/learn/how-to/premium-content).
2. Clipchamp: [스톡 미리보기 UI](https://support.microsoft.com/en-us/clipchamp/how-to-add-stock-videos-to-a-video), [Export 제한](https://support.microsoft.com/en-gb/clipchamp/exporting-and-saving-a-video-in-clipchamp).
3. Zapier: [Premium 앱 목록](https://zapier.com/apps/categories/premium), [Premium 태그](https://help.zapier.com/hc/en-us/articles/37982571569421-What-is-a-premium-app), [게시 시 업그레이드](https://help.zapier.com/hc/en-us/articles/35201208823181-Why-do-I-need-to-upgrade-to-publish-my-Zap).
4. Wix: [App Market](https://www.wix.com/app-market), [Stores 설치와 주문 조건](https://support.wix.com/en/article/upgrading-wix-stores).
5. Canva: [Premium Apps 가이드](https://www.canva.dev/docs/apps/design-guidelines/premium-apps/), [Premium 요소 미리보기](https://www.canva.com/help/preview-designs-with-premium-elements/).
6. CapCut: [플랫폼별 Pro 표시·제한 안내](https://www.capcut.com/help/why-prompted-to-purchase-capcut-pro).
7. Figma: [플러그인 사용](https://help.figma.com/hc/en-us/articles/360042532714-Use-plugins-in-files), [체험과 구매](https://help.figma.com/hc/en-us/articles/11786473291159-Purchase-Community-resources), [Super Spline 설명 예시](https://www.figma.com/community/plugin/1662164406339904290/super-spline).
8. VEED: [Dashboard](https://support.veed.io/en/articles/11641509-how-veed-s-dashboard-works), [AI Playground](https://support.veed.io/en/articles/11712887-how-to-use-veed-s-ai-playground).
9. Descript: [Export 설정](https://help.descript.com/export-and-share/video-gif), [AI 비용 UI](https://help.descript.com/billing-payments-plans/track-and-understand-your-media-minutes-and-ai-credits).
10. DaVinci: [공식 Resolve 20 Guide p.121](https://documents.blackmagicdesign.com/UserManuals/DaVinci-Resolve-20-Beginners-Guide.pdf).
11. Raycast: [스토어 UI](https://manual.raycast.com/extensions), [Pro Extension Models](https://manual.raycast.com/ai/extension-models).
12. Miro: [마켓 가격 표시 구분](https://developers.miro.com/docs/provide-pricing-details-for-your-app), [Jira Cards](https://miro.com/marketplace/jira/).
13. JetBrains: [목록](https://plugins.jetbrains.com/), [Freemium](https://plugins.jetbrains.com/docs/marketplace/freemium.html), [상세·가격](https://plugins.jetbrains.com/plugin/19668-gerry-themes-pro/pricing).
14. Atlassian: [ScriptRunner 상세·가격](https://marketplace.atlassian.com/apps/6820/scriptrunner-for-jira?hosting=cloud&tab=pricing), [설치 안내](https://support.atlassian.com/organization-administration/docs/installing-and-managing-app-access/).
15. Shopify: [Judge.me 상세](https://apps.shopify.com/judgeme), [목록 가격 표시](https://shopify.dev/docs/apps/launch/shopify-app-store/best-practices).
16. Framer: [플러그인 목록](https://www.framer.com/marketplace/plugins/), [Paid 목록](https://www.framer.com/marketplace/plugins/explore/paid/), [Frameship 상세](https://www.framer.com/marketplace/plugins/frameship/).
17. monday: [상세 예시](https://monday.com/marketplace/listing/19/analytics-reports), [체험/구매](https://support.monday.com/hc/en-us/articles/22579591539346-Apps-marketplace-billing-purchasing-an-app).

## 7. 확인 범위

일부 공개 마켓은 실제 브라우저로 목록·상세·가격을 읽었고, 로그인 계정 내 설치·결제·실행 제한은 공식 문서로 확인했다. Zapier 공개 목록에서는 카드 옆 Premium 태그를 직접 확인했다. Canva·Adobe·CapCut 화면은 공식 가이드 이미지이며 사용자 계정에서 재현한 것이 아니다. 서비스마다 같은 정책이라고 묶지 않는다.

이번 기록은 참고 자료와 제안이다. 실제 Clipper UI 변경·등급별 검사 구현·동기화 재개가 아니다. 기존 회원 웹 가격 카드의 관리자 데이터 연결과 요금제 설정 정본 원칙은 유지한다.
