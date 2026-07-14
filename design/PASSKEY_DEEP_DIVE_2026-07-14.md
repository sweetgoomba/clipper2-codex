# 패스키 심화 학습 노트

기준일: 2026-07-14 KST

이 문서는 패스키를 단순히 `지문으로 로그인하는 기능`으로 이해하는 단계에서 벗어나, 패스키의 역사, 표준, 암호학적 동작, 종류, 플랫폼별 차이, 보안 효과와 한계, 실제 제품에서의 구현 경계까지 체계적으로 학습하기 위한 문서다.

Clipper Studio의 Electron YouTube 로그인 창에 관한 구체적인 버전 검토와 도입 조건은 별도 문서인 [Electron YouTube 로그인 패스키 지원 검토](ELECTRON_YOUTUBE_PASSKEY_SUPPORT_REVIEW_2026-07-14.md)를 함께 본다.

## 1. 가장 먼저 바로잡을 핵심 개념

패스키는 지문, 얼굴, PIN, Mac 로그인 암호 그 자체가 아니다.

패스키의 실체는 특정 웹사이트 또는 앱 계정용으로 생성된 `공개키·개인키 쌍을 사용하는 FIDO 자격 증명`이다. 지문, 얼굴, 기기 PIN, 화면 잠금 패턴, 기기 암호는 그 개인키를 지금 사용해도 되는 사람인지 기기 안에서 확인하는 `로컬 사용자 검증 수단`이다.

예를 들어 MacBook Pro에서 Google 패스키 로그인을 할 때 일어나는 일은 다음과 같다.

1. Google이 이 로그인 요청만을 위한 임의의 challenge를 보낸다.
2. Mac은 `google.com`용 패스키를 찾는다.
3. Touch ID로 사용자를 로컬에서 확인한다.
4. Mac 안의 개인키가 challenge와 요청 정보를 서명한다.
5. Google은 미리 등록된 공개키로 서명을 검증한다.

Touch ID 지문 데이터가 Google로 전송되는 것도 아니고, 지문 자체가 Google 계정의 패스키인 것도 아니다.

Touch ID가 없는 Mac mini에서 Mac 로그인 암호를 입력해 패스키 사용을 승인하는 경우도 같은 원리다. 입력한 Mac 암호는 웹사이트 비밀번호로 Google에 전달되지 않는다. macOS가 로컬에서 사용자임을 확인한 후 패스키 개인키 사용을 허용할 뿐이다.

한 문장으로 줄이면 다음과 같다.

> 패스키는 기기에 보관된 암호학적 로그인 자격 증명이고, 지문·얼굴·PIN·기기 암호는 그 자격 증명을 꺼내 쓰기 위한 로컬 잠금 해제 수단이다.

## 2. 패스키란 무엇인가

[FIDO Alliance의 공식 정의](https://fidoalliance.org/passkeys/)에 따르면 패스키는 FIDO 표준에 기반한 인증 자격 증명이며, 사용자가 기기를 잠금 해제할 때 쓰는 생체 인식, PIN, 패턴 등의 과정으로 앱과 웹사이트에 로그인하게 해준다.

패스키에는 다음 성질이 있다.

- 특정 서비스의 특정 계정에 연결된다.
- 서비스마다 서로 다른 키 쌍을 사용한다.
- 서버에는 공개키가 등록되고, 서명을 만드는 개인키는 서버에 전달되지 않는다.
- 사람이 기억하거나 직접 입력하는 공유 비밀이 아니다.
- 올바르게 구현되면 가짜 도메인에서 사용할 수 없어 피싱에 강하다.
- 동기화 제공자를 통해 여러 기기에 동기화할 수도 있고, 한 기기 또는 보안 키에만 묶을 수도 있다.

`passkey`는 Apple만의 상품명이 아니다. FIDO Alliance가 정의한 크로스 플랫폼 일반 명사다. Apple, Google, Microsoft, 여러 비밀번호 관리자가 같은 FIDO/WebAuthn 기반 개념을 각 플랫폼에서 제공한다.

## 3. 왜 패스키가 등장했는가

기존 비밀번호 방식은 구조적으로 다음 문제가 있다.

### 3.1 서버와 사용자가 같은 비밀을 취급한다

사용자는 비밀번호를 입력하고 서버는 그 비밀번호를 검증할 수 있는 정보를 보관한다. 서버가 원문 대신 안전한 password hash를 저장하더라도, 약한 비밀번호나 재사용된 비밀번호는 유출 후 크리덴셜 스터핑 공격에 악용될 수 있다.

### 3.2 사용자가 가짜 사이트에 비밀번호를 넘길 수 있다

비밀번호는 사용자가 어느 입력창에든 타이핑할 수 있다. 공격자가 진짜와 비슷한 로그인 화면을 만들면 사용자가 스스로 비밀번호와 OTP를 제공할 수 있다.

### 3.3 기억하기 어려워 재사용과 약한 선택을 유도한다

서비스마다 고유하고 긴 비밀번호를 기억하기 어렵기 때문에 재사용, 단순한 패턴, 메모, 빈번한 재설정이 발생한다.

### 3.4 전통적인 2단계 인증도 항상 피싱 방지형은 아니다

SMS 코드와 TOTP 같은 일회용 코드는 재사용 공격에는 비교적 강하지만, 공격자가 실시간으로 코드를 받아 진짜 사이트에 중계하는 피싱에는 취약할 수 있다. 휴대전화 승인도 사용자가 요청 내용을 제대로 보지 않고 승인하는 MFA fatigue 공격을 받을 수 있다.

패스키는 서버와 공유하는 비밀번호를 없애고, 서비스 도메인에 묶인 공개키 암호화를 사용해 이 문제를 줄이려는 기술이다. NIST도 [SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/)에서 WebAuthn/FIDO2를 verifier name binding으로 피싱 저항성을 제공하는 대표적인 표준으로 설명한다.

## 4. 누가, 언제 만들었는가

패스키는 한 회사나 한 사람이 한 번에 만든 기능이 아니다. FIDO Alliance, W3C, 브라우저·운영체제·보안 하드웨어 업체들이 여러 단계에 걸쳐 만든 공개 표준 생태계의 결과다.

### 4.1 주요 연혁

| 시기 | 사건 | 의미 |
| --- | --- | --- |
| 2012년 7월 | FIDO Alliance 결성 | 강력한 인증 기술 사이의 상호운용성 부족과 비밀번호 문제를 해결하기 위한 산업 연합 시작 |
| 2013년 2월 12일 | FIDO Alliance 공개 출범 | Agnitio, Infineon, Lenovo, Nok Nok Labs, PayPal, Validity가 창립 조직으로 공개됨 |
| 2014년 전후 | UAF·U2F 초기 상용 배포 | 모바일 생체 인증과 USB 보안 키 기반의 비밀번호 보완·대체가 실제 제품에 도입됨 |
| 2015~2018년 | FIDO2와 WebAuthn 협력 발전 | 브라우저와 웹서비스가 공통 API로 공개키 인증을 사용할 수 있는 구조 정립 |
| 2019년 3월 4일 | WebAuthn이 W3C Recommendation이 됨 | 웹 표준으로서의 기반이 공식화됨. CTAP과 함께 FIDO2 구성 |
| 2022년 3월 | Multi-Device FIDO Credentials 백서 | 자격 증명 동기화를 통해 기기 교체와 복구 문제를 줄이는 방향 제시 |
| 2022년 5월 5일 | Apple·Google·Microsoft 공동 발표 | 여러 기기 동기화와 휴대전화 교차 기기 인증을 포함한 확장 지원을 공동 약속 |
| 2022년 이후 | `passkey` 명칭과 소비자 구현 확산 | iCloud Keychain, Google Password Manager, Windows와 제3자 관리자로 보편화 |
| 2025년 이후 | 자격 증명 관리자 간 교환 표준 발전 | 제공자 종속을 줄이기 위한 안전한 import/export 표준과 플랫폼 지원이 확장 중 |

[FIDO Alliance의 2013년 출범 보도자료](https://fidoalliance.org/assets/downloads/FIDO_Alliance_launch__FINAL__02_12_13docx.pdf)는 당시 비밀번호 재사용, 악성코드, 피싱 문제를 직접적인 출범 이유로 설명한다. FIDO는 `Fast IDentity Online`의 약자다.

2019년에는 [W3C와 FIDO Alliance가 WebAuthn 표준 완성을 발표](https://www.w3.org/press-releases/2019/webauthn/)했다. 2022년에는 [Apple, Google, Microsoft가 FIDO의 확장된 비밀번호 없는 로그인 지원을 공동 발표](https://fidoalliance.org/apple-google-and-microsoft-commit-to-expanded-support-for-fido-standard-to-accelerate-availability-of-passwordless-sign-ins/)하면서 오늘날의 동기화형 패스키와 교차 기기 UX가 본격적으로 확산됐다.

따라서 `누가 만들었는가`에 대한 가장 정확한 답은 다음과 같다.

> FIDO Alliance가 인증기와 클라이언트 프로토콜을 산업 표준으로 만들고, W3C가 브라우저용 WebAuthn API를 표준화했으며, Apple·Google·Microsoft와 브라우저·보안 업체들이 운영체제와 제품에 구현했다.

## 5. 패스키를 이루는 표준 계층

패스키 자체를 별도의 완전히 새로운 프로토콜 하나로 생각하면 안 된다. 패스키는 기존 FIDO2/WebAuthn 표준을 사용하기 쉽게 제품화한 자격 증명과 UX 개념이다.

### 5.1 WebAuthn

[Web Authentication API, WebAuthn](https://www.w3.org/TR/webauthn-3/)은 웹사이트가 브라우저를 통해 공개키 자격 증명을 생성하고 사용하는 API와 데이터 구조를 정의한다.

대표적인 호출은 다음 두 가지다.

- 등록: `navigator.credentials.create()`
- 인증: `navigator.credentials.get()`

브라우저는 호출한 origin과 RP ID를 검사하고, 운영체제나 보안 키의 인증기와 통신한다. 웹페이지 JavaScript가 개인키를 직접 읽지는 못한다.

### 5.2 CTAP

CTAP는 Client to Authenticator Protocol의 약자다. 브라우저나 운영체제 같은 클라이언트가 외장 보안 키, 휴대전화 등 인증기와 통신하는 방법을 정의한다.

- USB 보안 키
- NFC 보안 키
- Bluetooth를 활용한 근접 확인
- QR 코드로 시작하는 휴대전화 교차 기기 인증

등의 경로가 CTAP 계층과 관련된다.

### 5.3 FIDO2

FIDO2는 일반적으로 다음 두 축을 함께 가리킨다.

- W3C WebAuthn: 웹 애플리케이션과 브라우저 사이의 API
- FIDO Alliance CTAP: 클라이언트와 인증기 사이의 통신

[FIDO Alliance의 인증 표준 안내](https://fidoalliance.org/specifications/)에서 UAF, U2F, CTAP 등 FIDO 계열 표준을 확인할 수 있다.

### 5.4 패스키 제공자

패스키 제공자 또는 자격 증명 관리자는 패스키를 생성하고 보관하며 사용자에게 선택 UI를 제공한다.

예시는 다음과 같다.

- Apple Passwords와 iCloud Keychain
- Google Password Manager
- Microsoft Password Manager
- 1Password, Dashlane 같은 제3자 관리자
- 운영체제의 로컬 플랫폼 인증기
- FIDO2 하드웨어 보안 키

브라우저, 운영체제, 확장 프로그램, 독립 앱 중 하나 또는 여러 계층이 함께 제공자 역할을 할 수 있다.

## 6. 주요 구성 요소와 역할

| 용어 | 의미 | Google 로그인 예시 |
| --- | --- | --- |
| 사용자 | 로그인하려는 사람 | Google 계정 사용자 |
| Relying Party, RP | 패스키를 받아 인증하는 서비스 | Google |
| RP ID | 패스키가 묶이는 서비스 식별 도메인 | 보통 `google.com` 계열의 허용된 RP ID |
| Origin | 실제 요청 페이지의 scheme, host, port 조합 | `https://accounts.google.com` 같은 origin |
| Client/User Agent | WebAuthn 요청을 처리하는 브라우저·앱 | Safari, Chrome, Edge, Electron Chromium |
| Authenticator | 키를 만들고 서명을 수행하는 구성 요소 | Touch ID/Secure Enclave, Windows Hello, 휴대전화, 보안 키 |
| Credential provider | 패스키 저장·동기화·선택을 관리 | iCloud Keychain, Google Password Manager |
| Verifier | 공개키로 응답을 검증하는 서버 | Google 인증 서버 |

운영체제의 로그인 화면, 브라우저의 패스키 선택 UI, 비밀번호 관리자의 저장소가 한 화면처럼 보일 수 있지만 실제로는 서로 다른 역할을 맡는다.

## 7. 패스키 등록은 어떻게 동작하는가

패스키를 새로 만드는 과정을 registration 또는 credential creation ceremony라고 한다.

```text
웹사이트/RP 서버
  │  1. challenge, RP 정보, 사용자 식별 정보 전달
  ▼
브라우저/WebAuthn client
  │  2. 사용할 인증기·패스키 제공자 선택
  ▼
인증기
  │  3. 지문·얼굴·PIN 등으로 로컬 사용자 검증
  │  4. 해당 RP 전용 공개키·개인키 쌍 생성
  │  5. 개인키는 인증기/제공자에 보관
  ▼
브라우저
  │  6. credential ID, 공개키, 검증 데이터 반환
  ▼
RP 서버
     7. challenge, origin, RP ID 등을 검증하고 공개키 저장
```

핵심은 서버가 개인키를 받지 않는다는 점이다. 서버 데이터베이스에는 보통 계정과 연결된 credential ID, 공개키, 관련 메타데이터가 저장된다.

동기화형 패스키라면 개인키 재료가 패스키 제공자의 동기화 저장소에 종단 간 암호화된 형태로 복제될 수 있다. 이 경우에도 RP 서버로 개인키가 전달되는 것은 아니다. `개인키가 절대 어느 기기에서도 나가지 않는다`는 설명은 장치 귀속형 패스키에는 맞지만 모든 동기화형 패스키에 그대로 적용하면 부정확하다.

## 8. 패스키 로그인은 어떻게 동작하는가

기존 패스키로 로그인하는 과정을 authentication 또는 assertion ceremony라고 한다.

```text
RP 서버
  │  1. 매번 새 challenge 생성
  ▼
브라우저/WebAuthn client
  │  2. 현재 origin과 RP ID를 확인
  │  3. 사용할 패스키·인증기 선택
  ▼
인증기
  │  4. 사용자 존재(UP), 필요하면 사용자 검증(UV) 확인
  │  5. RP 전용 개인키로 요청 데이터 서명
  ▼
RP 서버
     6. 등록된 공개키로 서명 검증
     7. challenge, origin, RP ID, UP/UV 정책 검증
     8. 성공하면 일반적인 로그인 세션 발급
```

challenge는 로그인 요청마다 새로 만들어지는 임의 값이다. 과거의 정상 서명 응답을 녹화해 재전송해도 현재 challenge와 맞지 않으므로 replay 공격을 막는 데 도움을 준다.

서명 대상에는 challenge만 덩그러니 들어가는 것이 아니다. WebAuthn client data와 authenticator data를 통해 요청 종류, origin, RP ID와 연결된 정보, 사용자 검증 상태 등이 함께 검증된다.

## 9. 지문·얼굴·PIN·기기 암호는 각각 무엇인가

이 부분이 가장 자주 혼동된다.

| 사용자가 하는 행동 | 실제 역할 | 웹사이트로 전달되는가 |
| --- | --- | --- |
| Touch ID 지문 인식 | 기기 안에서 개인키 사용자를 확인 | 지문 원본·템플릿은 전달되지 않음 |
| Face ID/Windows Hello 얼굴 인식 | 기기 안에서 사용자 검증 | 얼굴 데이터는 전달되지 않음 |
| Windows Hello PIN | 해당 Windows 기기의 보호된 키 사용 승인 | PIN은 웹사이트에 전달되지 않음 |
| 휴대전화 화면 잠금 PIN·패턴 | 휴대전화의 패스키 사용 승인 | PIN·패턴은 전달되지 않음 |
| Mac 로그인 암호 | macOS 로컬 사용자 확인과 자격 증명 사용 승인에 쓰일 수 있음 | Google 비밀번호처럼 전송되지 않음 |
| 보안 키 PIN | 물리 보안 키 안의 자격 증명 잠금 해제 | RP의 계정 비밀번호로 전송되지 않음 |

운영체제는 로컬 검증 성공 여부를 WebAuthn 결과의 UV, 즉 User Verified 상태로 표현할 수 있다. 서비스는 로그인 정책에 따라 UV를 필수로 요구할 수 있다.

지문 인식이 실패해 PIN이나 기기 암호를 입력했다고 해서 다른 패스키로 로그인하는 것은 아니다. 같은 패스키 개인키를 사용하는데 로컬 사용자 검증 수단만 바뀔 수 있다.

## 10. 패스키의 종류

패스키 종류는 한 가지 축으로만 나뉘지 않는다. `어디에 저장되는가`, `어떤 인증기를 쓰는가`, `계정을 스스로 발견할 수 있는가`, `어느 기기에서 쓰는가`를 별도로 봐야 한다.

### 10.1 저장·복제 기준: 동기화형과 장치 귀속형

#### 동기화형 패스키, synced passkey

- 제공자의 암호화된 동기화 영역을 통해 여러 승인된 기기에서 사용할 수 있다.
- 새 휴대전화나 컴퓨터로 바꿔도 같은 제공자 계정을 복구하면 패스키를 다시 사용할 수 있다.
- iCloud Keychain, Google Password Manager, Microsoft Password Manager, 지원되는 제3자 관리자가 대표적이다.
- 편의성과 복구성이 높다.
- 동기화 제공자 계정과 그 계정 복구 절차가 중요한 신뢰 경계가 된다.

NIST는 [동기화형 인증기 지침](https://pages.nist.gov/800-63-4/sp800-63b/syncable/)에서 동기화 저장소의 키 재료를 강하게 암호화하고, 동기화 저장소 접근을 AAL2 수준의 다중 요소 인증으로 보호하며, 사용자에게 동기화 위치와 상태를 확인할 UI를 제공하도록 요구·권고한다.

#### 장치 귀속형 패스키, device-bound passkey

- 개인키가 특정 기기 또는 물리 보안 키를 떠나지 않도록 설계된다.
- 다른 기기로 자동 동기화되지 않는다.
- TPM, Secure Enclave, 독립 보안 키 같은 보호 하드웨어에 묶을 수 있다.
- 높은 통제와 비수출성을 제공할 수 있지만, 분실·고장에 대비해 별도 인증기나 복구 절차가 필요하다.

동기화형이 무조건 약하고 장치 귀속형이 무조건 정답인 것은 아니다. 소비자 서비스에서는 복구성과 사용성이 중요하고, 일부 고보증 기업 환경에서는 비수출형 하드웨어 자격 증명이 필요할 수 있다. NIST SP 800-63B-4에서 동기화 가능한 키는 조건을 충족하면 AAL2에 사용할 수 있지만, 키 비수출성이 필요한 AAL3에는 사용할 수 없다고 구분한다.

### 10.2 인증기 위치 기준: 플랫폼 인증기와 로밍 인증기

#### 플랫폼 인증기, platform authenticator

현재 사용하는 기기에 내장된 인증기다.

- Mac의 Touch ID/Secure Enclave 기반 인증
- iPhone의 Face ID/Touch ID 기반 인증
- Windows Hello와 TPM
- Android 기기의 화면 잠금과 하드웨어 키 저장소

#### 로밍·크로스 플랫폼 인증기, roaming/cross-platform authenticator

컴퓨터와 분리되어 여러 기기에 연결해 사용할 수 있다.

- USB FIDO2 보안 키
- NFC 보안 키
- Bluetooth를 이용하는 외부 인증기
- 다른 기기 로그인에 사용하는 휴대전화

`플랫폼 인증기 = 동기화형`, `보안 키 = 항상 비동기화형`처럼 두 축을 하나로 합치면 안 된다. 플랫폼의 패스키가 클라우드로 동기화될 수도 있고, 플랫폼에만 묶일 수도 있다.

### 10.3 계정 발견 기준: 발견 가능 자격 증명

발견 가능 자격 증명, discoverable credential은 서버가 먼저 credential ID 목록을 주지 않아도 인증기가 RP ID를 기준으로 계정 후보를 찾아 사용자에게 보여줄 수 있는 자격 증명이다. 과거에는 resident key라는 표현도 널리 쓰였다.

이 기능 덕분에 다음 UX가 가능하다.

- 이메일이나 사용자 이름을 먼저 입력하지 않고 `패스키로 로그인`
- 한 서비스의 여러 계정 중 사용할 계정 선택
- 입력창 자동 완성 목록에 패스키 계정 표시

현대적인 패스키는 일반적으로 발견 가능한 FIDO 자격 증명을 전제로 하지만, 모든 과거 WebAuthn 자격 증명이 오늘날 말하는 패스키 UX를 제공하는 것은 아니다.

### 10.4 사용 위치 기준: 같은 기기와 교차 기기

- 같은 기기 인증: 노트북에 저장된 패스키를 그 노트북에서 사용
- 교차 기기 인증: 컴퓨터 화면의 QR 코드를 휴대전화로 스캔하고, 휴대전화 패스키로 컴퓨터 로그인을 승인

교차 기기 인증은 새로운 종류의 패스키가 아니라 `다른 기기에 있는 패스키를 현재 로그인에 사용하는 전송 방식`이다. 패스키가 휴대전화에서 컴퓨터로 복사되는 것으로 이해하면 안 된다.

### 10.5 실제 조합 예시

| 사례 | 동기화 여부 | 인증기 형태 | 사용 방식 |
| --- | --- | --- | --- |
| iCloud Keychain에 저장된 Google 패스키 | 동기화형 | Apple 플랫폼/제공자 | Mac·iPhone 등 승인된 Apple 기기에서 사용 |
| Google Password Manager 패스키 | 동기화형 | Android/Chrome 계열 제공자 | 동기화 기기 또는 교차 기기에서 사용 |
| Windows Hello에 로컬 저장 | 장치 귀속형 | Windows 플랫폼 인증기 | 해당 Windows PC에서 얼굴·지문·PIN으로 사용 |
| Microsoft Password Manager 저장 | 동기화형 | 자격 증명 관리자 | 승인된 환경에 동기화해 사용 |
| FIDO2 USB 보안 키 | 보통 장치 귀속형 | 로밍 인증기 | USB/NFC로 여러 컴퓨터에서 사용 |
| 휴대전화 QR 로그인 | 원래 저장 방식 유지 | 휴대전화가 외부 인증기 역할 | 근처 컴퓨터 로그인만 승인 |
| Electron macOS Touch ID WebAuthn 자격 증명 | 장치 귀속형 | Electron이 활성화한 플랫폼 인증기 | 해당 Mac과 Electron 세션 파티션 범위에서 사용 |

마지막 행은 일반 Safari/iCloud 패스키와 같지 않다. Electron의 현재 API가 만드는 Touch ID 자격 증명은 기기 귀속형이며 iCloud Keychain 동기화형 패스키로 취급되지 않는다.

## 11. macOS와 Apple 기기에서의 패스키

Apple의 일반 사용자용 패스키는 주로 iCloud Keychain과 Passwords 앱을 통해 관리된다.

[Apple Passkeys 안내](https://developer.apple.com/passkeys/)에 따르면 Apple 플랫폼의 패스키는 FIDO Alliance와 W3C 표준에 기반하며, 공개키·개인키 쌍을 사용하고 iCloud Keychain의 패스키는 종단 간 암호화된다.

### 11.1 MacBook Pro에 Touch ID가 있는 경우

Touch ID는 패스키 개인키 사용을 승인하는 로컬 사용자 검증 수단이다. 패스키가 iCloud Keychain에 동기화되어 있다면 같은 Apple 계정의 승인된 기기에서 사용할 수 있다.

### 11.2 Mac mini처럼 Touch ID가 없는 경우

가능한 경로는 OS 버전, 브라우저, 연결된 주변기기, 패스키 제공자에 따라 달라질 수 있다.

- Mac 로그인 암호로 로컬 승인
- Touch ID가 있는 Magic Keyboard 사용
- iPhone 또는 iPad의 패스키를 QR 코드로 사용
- 외장 FIDO2 보안 키 사용
- 제3자 패스키 제공자 사용

여기서 Mac 로그인 암호를 입력하더라도 웹사이트 계정 비밀번호를 입력하는 것이 아니다.

### 11.3 iCloud 동기화와 보안

[Apple Passwords 공식 안내](https://support.apple.com/en-us/120758)에 따르면 iCloud Keychain은 승인된 Apple 기기 사이에서 패스키를 사용할 수 있게 한다. 동기화 편의성은 기기 교체에 유리하지만 Apple 계정, 승인된 기기, 복구 절차가 전체 보안 모델의 일부가 된다.

### 11.4 Safari에서 되는데 Electron에서 안 될 수 있는 이유

패스키 성공 여부는 웹사이트 지원만으로 결정되지 않는다. 다음 계층이 모두 맞아야 한다.

- Google 같은 RP가 WebAuthn 요청을 올바르게 제공
- Chromium/Electron이 필요한 WebAuthn 기능을 지원
- Electron 앱이 플랫폼 인증기를 활성화하고 이벤트를 처리
- macOS 앱의 서명과 keychain entitlement가 올바름
- 현재 Electron 세션 파티션에서 사용 가능한 자격 증명이 존재
- OS와 하드웨어가 해당 인증 방식을 지원

따라서 Safari에서 iCloud 패스키가 보인다고 해서 임의의 Electron 로그인 창에서도 동일한 패스키 목록과 Touch ID 흐름이 자동으로 동작하는 것은 아니다.

## 12. Windows에도 패스키가 있는가

있다. Windows에서도 패스키를 사용해 Microsoft 계정뿐 아니라 WebAuthn을 지원하는 다른 웹사이트와 앱에 로그인할 수 있다.

[Microsoft의 패스키 생성·저장 안내](https://support.microsoft.com/en-us/windows/synchronize-passkeys-to-your-microsoft-account-be9de83c-6803-4ccc-81f2-e1fcc2fb8110)는 Windows에서 다음 저장 위치를 설명한다.

- Microsoft Password Manager 또는 다른 동기화형 자격 증명 관리자
- iPhone, iPad, Android 기기
- 물리 FIDO2 보안 키
- Windows 기기 로컬의 Windows Hello

### 12.1 Windows Hello와 패스키의 관계

Windows Hello는 얼굴, 지문, PIN으로 Windows 사용자와 보호된 키 사용을 확인하는 플랫폼 인증 체계다. WebAuthn 웹사이트용 패스키가 Windows Hello에 로컬 저장되면, 얼굴·지문·PIN으로 그 패스키 사용을 승인할 수 있다.

[Microsoft의 Windows 11 보안 문서](https://learn.microsoft.com/en-us/windows/security/book/identity-protection-passwordless-sign-in)는 Windows Hello가 TPM에 비대칭 키를 결합하고, PIN이나 생체 인식으로 사용자를 확인한 뒤 키 사용을 허용한다고 설명한다.

### 12.2 Windows 로그인과 웹사이트 패스키 로그인은 같은가

같은 Windows Hello UI와 로컬 검증 수단을 사용할 수 있지만 인증 대상은 다르다.

- Windows 로그인: 이 PC의 Windows 사용자 세션을 연다.
- 웹사이트 패스키 로그인: 특정 RP용 개인키로 웹사이트 challenge에 서명한다.

Windows Hello PIN은 Microsoft 계정 비밀번호의 짧은 대체 문자열이 아니다. 해당 기기의 보호된 자격 증명을 잠금 해제하는 로컬 비밀이다. 같은 Microsoft 계정으로 로그인한 다른 PC의 Windows Hello PIN과 같을 필요도 없다.

### 12.3 Windows Hello 로컬 저장과 동기화형 저장

Microsoft 문서는 `Windows device / Windows Hello` 저장을 해당 Windows 기기에 로컬 저장하는 방식으로 구분한다. 반면 Microsoft Password Manager나 다른 동기화형 관리자를 선택하면 제공자의 정책에 따라 여러 환경에서 사용할 수 있다.

즉 Windows에서 보이는 `패스키`도 모두 같은 저장 방식은 아니다. 저장 화면에서 어디에 저장되는지 확인해야 한다.

### 12.4 Windows에서 휴대전화나 보안 키 사용

Windows PC 로그인 화면이나 브라우저의 WebAuthn UI에서 QR 코드를 스캔해 iPhone/Android 패스키를 사용할 수 있고, USB/NFC FIDO2 보안 키를 사용할 수도 있다. 휴대전화 교차 기기 인증은 근접 확인을 위해 Bluetooth를 요구할 수 있다.

## 13. Android와 Google 생태계

Android에서는 Google Password Manager 또는 지원되는 제3자 제공자가 패스키를 관리할 수 있다. 화면 잠금 지문, 얼굴, PIN, 패턴 등이 로컬 사용자 검증에 사용된다.

[Google 계정 패스키 공식 안내](https://support.google.com/accounts/answer/13548313)는 Google 패스키 로그인에 지문, 얼굴, 휴대전화 화면 잠금 PIN을 사용할 수 있으며 생체 정보가 Google로 전송되지 않는다고 설명한다.

Google 계정에서 패스키를 사용하면 계정 설정에 따라 비밀번호와 별도의 두 번째 단계를 대신할 수 있다. 다만 다음 사항은 별개다.

- Google 계정이 패스키 우선 로그인을 사용하도록 설정됐는가
- 조직의 Google Workspace 관리자가 패스키 단독 로그인을 허용하는가
- 현재 브라우저·앱이 패스키 방식을 지원하는가
- 해당 기기 또는 제공자에 사용할 수 있는 패스키가 있는가
- 위험 기반 인증 때문에 Google이 추가 확인을 요구하는가

Google은 패스키가 동작하지 않을 때 `다른 방법 시도`로 비밀번호나 다른 인증 수단을 선택할 수 있는 경로도 제공한다. 패스키가 있다고 해서 모든 계정 복구 수단과 기존 인증 수단이 자동으로 삭제되는 것은 아니다.

## 14. 물리 보안 키와 패스키

YubiKey 같은 FIDO2 보안 키에도 패스키를 저장할 수 있다.

일반적인 흐름은 다음과 같다.

1. USB 또는 NFC로 보안 키를 연결한다.
2. 필요하면 보안 키 PIN을 입력한다.
3. 보안 키를 터치하거나, 지문 센서가 있는 모델이면 지문을 확인한다.
4. 보안 키 내부 개인키가 WebAuthn 요청에 서명한다.

장점은 개인키를 특정 하드웨어에 강하게 묶을 수 있고 운영체제 계정 동기화에 의존하지 않는다는 점이다. 단점은 분실, 파손, 휴대 부담, 저장 가능한 자격 증명 수, 복구 키 관리다. 중요한 계정이라면 보안 키 하나만 등록하고 끝내기보다 예비 보안 키나 별도의 안전한 복구 방법을 준비해야 한다.

과거의 U2F 보안 키가 모두 곧바로 `패스키 저장 가능 보안 키`인 것은 아니다. 발견 가능한 자격 증명과 FIDO2 기능을 지원하는지 확인해야 한다.

## 15. 휴대전화로 다른 기기에 로그인하는 원리

컴퓨터에서 패스키 로그인을 선택했는데 휴대전화로 QR 코드를 스캔하라는 화면이 나올 수 있다.

대략적인 흐름은 다음과 같다.

1. 컴퓨터가 일회성 연결 정보를 QR 코드로 표시한다.
2. 휴대전화가 QR 코드를 읽는다.
3. Bluetooth Low Energy 등을 통해 두 기기가 가까이 있는지 확인한다.
4. 휴대전화에서 지문·얼굴·PIN으로 패스키 사용을 승인한다.
5. 휴대전화 인증기가 현재 WebAuthn 요청에 필요한 서명을 제공한다.
6. 컴퓨터의 로그인 흐름이 완료된다.

[FIDO Alliance의 설명](https://fidoalliance.org/passkeys/)과 [Google의 교차 기기 로그인 안내](https://support.google.com/accounts/answer/13548313)는 QR 코드와 Bluetooth 근접 확인을 사용하는 이 경로를 설명한다.

중요한 점은 다음과 같다.

- Bluetooth는 두 기기의 물리적 근접성을 확인하는 데 쓰인다.
- 휴대전화 패스키가 컴퓨터 저장소로 그대로 복사되는 과정은 아니다.
- 컴퓨터와 휴대전화가 서로 다른 운영체제여도 표준을 지원하면 사용할 수 있다.
- QR 코드는 매번 같거나 장기적으로 재사용하는 계정 비밀이 아니다.

## 16. 패스키가 피싱에 강한 이유

패스키의 피싱 저항성은 사용자가 로그인 화면을 잘 구별할 것이라는 기대가 아니라 프로토콜의 도메인 결합에 기반한다.

### 16.1 서비스마다 다른 키를 쓴다

`google.com`용 패스키와 공격자가 만든 `goog1e.example`용 패스키는 서로 다른 자격 증명이다. 비밀번호처럼 같은 문자열을 여러 서비스에서 재사용하지 않는다.

### 16.2 RP ID와 origin을 검증한다

브라우저는 현재 페이지의 origin과 RP ID 관계를 확인한다. 공격자 사이트는 진짜 Google RP ID용 개인키 서명을 마음대로 요청할 수 없다.

### 16.3 개인키를 웹페이지에 노출하지 않는다

JavaScript나 서버는 개인키 원문을 받지 않는다. 인증기는 요청에 서명한 결과만 제공한다.

### 16.4 매 요청에 새로운 challenge를 쓴다

공격자가 과거 로그인 응답을 탈취해도 다른 challenge의 새 로그인에 그대로 재사용할 수 없다.

이 때문에 패스키는 비밀번호, SMS OTP, TOTP보다 피싱과 replay에 강하다. 다만 `패스키를 쓰면 모든 피싱이 사라진다`는 뜻은 아니다. 로그인 후 세션을 훔치거나 사용자를 속여 송금·권한 변경을 유도하는 공격은 별도로 방어해야 한다.

## 17. 패스키는 다중 요소 인증인가

상황에 따라 그렇다고 볼 수 있지만 무조건 같은 문장으로 단정하면 안 된다.

패스키 인증에는 보통 다음 요소가 결합된다.

- 소유 요소: 개인키가 있는 기기, 보안 키 또는 동기화 제공자에 접근
- 활성화 요소: 지문·얼굴 같은 생체 정보 또는 기기 PIN·암호 같은 로컬 비밀

RP가 WebAuthn의 user verification을 요구하고 UV 성공을 검증하면 `가지고 있는 것 + 알고 있거나 신체적인 것`이 결합된 다중 요소 암호 인증으로 사용할 수 있다. Google은 이런 이유로 패스키가 계정 소유 기기와 잠금 해제를 함께 확인하므로 두 번째 인증 단계를 건너뛸 수 있다고 안내한다.

하지만 다음 경우는 구분해야 한다.

- RP가 사용자 존재, UP만 요구하고 UV를 요구하지 않는 경우
- 잠금 해제되지 않은 세션에서 추가 로컬 검증 없이 자격 증명을 사용하는 구현
- 조직 정책이 별도의 인증 요소나 위험 기반 확인을 추가로 요구하는 경우
- 패스키 뒤에 남아 있는 약한 비밀번호·SMS 계정 복구 경로

즉 `패스키라는 이름만 붙으면 자동으로 모든 보안 정책의 MFA 요구를 충족한다`고 가정하면 안 된다. RP 정책, UV 검증, 제공자와 복구 보안을 같이 봐야 한다.

## 18. 패스키가 막아주지 못하는 것

패스키는 강력하지만 만능은 아니다.

### 18.1 이미 열린 세션 탈취

패스키 로그인 후 서버는 보통 세션 쿠키나 토큰을 발급한다. 악성코드가 그 세션을 훔치거나 공격자가 이미 로그인된 기기를 장악하면 패스키를 다시 깨지 않고도 계정을 악용할 수 있다.

### 18.2 잠금 해제된 기기 사용

공유 기기에 패스키를 만들거나 다른 사람이 기기 잠금을 해제할 수 있다면 그 사람도 계정에 접근할 수 있다. Google도 개인 소유 기기에만 패스키를 만들라고 안내한다.

### 18.3 악성코드와 운영체제 침해

개인키 추출이 어렵더라도 악성코드가 사용자를 대신해 로그인 요청을 시작하거나 인증 후 세션과 데이터를 훔칠 수 있다. 하드웨어 보호는 중요한 완화책이지만 전체 기기 보안을 대신하지 않는다.

### 18.4 계정 복구 공격

패스키 로그인이 강해도 `비밀번호를 잊으셨나요`, 고객센터, 이메일 복구, SIM 기반 복구가 약하면 공격자는 더 쉬운 경로를 노린다. 보안은 가장 약한 허용 경로 수준으로 내려갈 수 있다.

### 18.5 동기화 제공자 계정 탈취

동기화형 패스키는 편리하지만 제공자 계정과 동기화 저장소 보호가 중요하다. 제공자 계정 복구가 탈취되면 여러 패스키에 대한 위험이 커질 수 있다.

### 18.6 잘못된 권한 부여

패스키는 `누가 로그인했는가`를 강하게 확인한다. 그 사용자가 어떤 데이터와 기능을 사용할 수 있는지는 애플리케이션의 authorization 문제다. 서버의 권한 검사 버그를 패스키가 고쳐주지는 않는다.

### 18.7 거래 내용 확인 부재

로그인 서명이 곧 특정 송금 금액이나 계약 내용을 승인했다는 뜻은 아니다. 고위험 작업에는 거래 내용과 결합된 별도 승인, 재인증, 감사 로그가 필요할 수 있다.

## 19. 동기화, 백업, 복구와 기기 분실

### 19.1 동기화형 패스키

새 기기에서 같은 패스키 제공자 계정을 안전하게 복구하면 승인된 패스키를 다시 사용할 수 있다. 편리하지만 제공자 계정의 MFA와 복구 정책이 중요하다.

### 19.2 장치 귀속형 패스키

기기를 잃으면 그 패스키도 사용할 수 없을 수 있다. 다음 중 하나 이상이 필요하다.

- 두 번째 기기에 별도 패스키 등록
- 예비 FIDO2 보안 키 등록
- 조직 관리자가 제공하는 안전한 재등록 절차
- 강하게 보호된 계정 복구 코드나 복구 절차

### 19.3 분실 시 해야 할 일

1. 남아 있는 신뢰 기기나 복구 수단으로 계정에 로그인한다.
2. 서비스 계정에서 분실 기기의 패스키를 제거한다.
3. 패스키 제공자 계정에서 분실 기기를 제거하거나 원격 잠금·삭제한다.
4. 활성 세션과 최근 보안 활동을 확인한다.
5. 필요하면 관련 세션을 모두 로그아웃시킨다.

서비스의 패스키 등록 정보와 패스키 제공자의 로컬 저장 항목은 서로 다른 목록일 수 있다. 서비스에서 패스키를 삭제했는데 관리자에 오래된 항목이 남거나, 관리자에서 지웠지만 서버 계정 등록 정보가 남는 상황을 구분해야 한다.

## 20. 개인정보와 추적 관점

WebAuthn은 서비스별 자격 증명을 사용하므로 같은 사용자의 패스키를 서로 다른 사이트가 공통 식별자로 직접 대조하기 어렵게 설계된다.

- 서비스 A와 서비스 B는 서로 다른 키 쌍과 credential ID를 본다.
- 생체 정보는 로컬 기기에 남고 RP는 생체 원본을 받지 않는다.
- RP는 공개키와 해당 계정에 필요한 식별 정보만 보관한다.
- WebAuthn user handle에는 이메일 같은 직접 식별 정보를 넣지 않는 것이 권장된다.

다만 개인정보 위험이 완전히 사라지는 것은 아니다.

- 서비스는 로그인 계정 자체를 당연히 식별한다.
- IP, 브라우저, 기기 신호, 기존 쿠키 등 다른 추적 수단이 남아 있다.
- attestation을 과도하게 요구하면 인증기 모델이나 조직 소유 장치 여부 같은 정보가 노출될 수 있다.
- 패스키 제공자는 사용자가 어떤 서비스의 자격 증명을 보유하는지 관리해야 하므로 제공자에 대한 신뢰가 필요하다.

## 21. Attestation과 Assertion의 차이

두 용어는 이름이 비슷하지만 다르다.

### 21.1 Attestation

패스키 등록 시 인증기가 어떤 종류이고 어떤 보안 특성을 가졌는지 RP가 판단할 수 있도록 제공하는 증명 정보다. 일반 소비자 서비스는 개인정보와 호환성을 위해 attestation을 요구하지 않거나 최소화하는 경우가 많다. 기업 관리 환경에서는 승인된 하드웨어만 허용하기 위해 enterprise attestation을 사용할 수 있다.

Attestation은 `이 사람의 실명은 누구다`를 증명하는 신분증이 아니다. 주로 자격 증명을 생성한 인증기의 출처와 특성에 관한 증명이다.

### 21.2 Assertion

이미 등록된 패스키로 로그인할 때 인증기가 challenge 등에 서명해 반환하는 인증 응답이다. 서버는 등록된 공개키로 assertion을 검증한다.

간단히 말하면 다음과 같다.

- attestation: 등록 시 `어떤 인증기가 이 키를 만들었는가`에 관한 선택적 증명
- assertion: 로그인 시 `등록된 개인키를 지금 실제로 사용할 수 있는가`에 관한 서명 응답

## 22. 패스키와 비밀번호 관리자

현대의 비밀번호 관리자는 비밀번호뿐 아니라 패스키 제공자 역할도 한다. 그러나 둘은 저장되는 자격 증명의 성격이 다르다.

| 구분 | 비밀번호 | 패스키 |
| --- | --- | --- |
| 사람이 읽고 입력 가능 | 가능 | 일반적으로 불가능 |
| 서버와 공유되는 비밀 | 있음 | 없음. 서버는 공개키 보유 |
| 다른 사이트에 재사용 | 사용자가 할 수 있음 | RP별 고유 키이므로 불가 |
| 가짜 사이트 입력 | 사용자가 넘길 수 있음 | origin/RP ID가 맞지 않으면 사용 제한 |
| 동기화 | 암호화 저장소로 가능 | 지원 제공자에서 암호화 동기화 가능 |

패스키 동기화는 실용성을 크게 높였지만 특정 제공자에 묶이는 문제가 생길 수 있다. FIDO Alliance는 [Credential Exchange Specifications](https://fidoalliance.org/specifications-credential-exchange-specifications/)에서 비밀번호와 패스키 등을 자격 증명 관리자 사이에 안전하게 이전하기 위한 표준 형식을 정의하고 있다. 실제 import/export 가능 범위는 운영체제, 관리자, 버전에 따라 다르므로 `표준이 존재한다`와 `내 환경에서 자유롭게 이동할 수 있다`를 구분해야 한다.

## 23. 패스키, OAuth, Google 로그인, 쿠키의 관계

이 네 가지는 서로 다른 계층이다.

### 23.1 패스키

Google이 사용자의 Google 계정을 인증하는 방법 중 하나다. 비밀번호와 2단계 인증 대신 또는 함께 사용될 수 있다.

### 23.2 Google 로그인 또는 OAuth/OIDC

애플리케이션이 Google을 신원 제공자 또는 권한 제공자로 사용해 사용자를 로그인시키거나 Google API 권한을 요청하는 프로토콜 흐름이다. Google이 사용자를 인증할 때 내부적으로 패스키, 비밀번호, 휴대전화 승인 중 무엇을 썼는지는 별도의 문제다.

### 23.3 세션 쿠키

Google 로그인이 끝나면 브라우저 세션을 유지하기 위해 쿠키가 생성될 수 있다. 이후 YouTube 웹 요청은 매번 패스키 서명을 요구하는 대신 이 로그인 세션 쿠키를 사용할 수 있다.

### 23.4 애플리케이션 자체 로그인

Clipper Studio 자체 계정 로그인은 Clipper Studio 서비스에 대한 인증이다. 영상용 YouTube 계정 로그인은 YouTube 콘텐츠 접근 권한을 위한 Google/YouTube 세션이다. 둘 다 화면에 Google 로그인이 나타날 수 있어도 대상 계정, 세션, 쿠키, 권한이 서로 다르다.

정리하면 다음과 같다.

```text
패스키/비밀번호/2단계 인증
        │
        ▼
Google이 Google 계정 사용자를 인증
        │
        ▼
Google/YouTube 브라우저 세션 쿠키 생성
        │
        ▼
Clipper Studio 영상용 Electron 세션과 관리 쿠키로 YouTube 접근
```

패스키를 지원한다고 해서 yt-dlp가 WebAuthn 개인키를 직접 사용하는 것은 아니다. Electron 로그인 창에서 Google 인증이 완료된 뒤 생성된 세션 쿠키를 Clipper Studio가 관리 파일로 내보내고, yt-dlp가 그 쿠키로 인증된 YouTube 요청을 수행한다.

## 24. 이번 Clipper Studio 현상을 패스키 관점에서 해석하기

현재 확인된 현상은 다음과 같다.

1. Clipper Studio가 Electron `persist:youtube-auth` 세션의 창에서 Google 로그인을 연다.
2. Google은 계정에 등록된 패스키를 우선 사용하려고 한다.
3. 현재 Electron 35 기반 로그인 창은 필요한 macOS 플랫폼 WebAuthn 경로를 완전히 구성하지 못해 `패스키를 사용하여 로그인을 완료합니다` 단계가 진행되지 않는다.
4. `다른 방법 시도`에서 비밀번호와 휴대전화 2단계 인증을 사용하면 Google 로그인이 완료된다.
5. 로그인 창을 닫으면 Electron 세션 쿠키가 관리 쿠키 파일로 내보내진다.
6. NestJS/yt-dlp는 이 관리 쿠키로 회원 전용·비공개 영상에 접근한다.

이 현상은 다음을 뜻하지 않는다.

- 사용자의 Mac에 패스키가 없다는 뜻이 아니다.
- Google 계정의 패스키가 깨졌다는 뜻이 아니다.
- macOS가 패스키를 전혀 지원하지 않는다는 뜻이 아니다.
- yt-dlp가 패스키 프로토콜을 직접 구현해야 한다는 뜻이 아니다.

문제 경계는 Google 로그인 WebAuthn 요청과 Electron/macOS 플랫폼 인증기 연결 사이에 있다. Electron 버전 업그레이드 외에도 앱 설정, entitlement, 서명, 세션 파티션, 복수 계정 선택 이벤트, macOS/Windows packaged QA가 필요하다. 구체적인 재개 조건은 [Electron YouTube 로그인 패스키 지원 검토](ELECTRON_YOUTUBE_PASSKEY_SUPPORT_REVIEW_2026-07-14.md)를 따른다.

## 25. 서비스를 직접 구현할 때의 핵심 원칙

Clipper Studio 자체 로그인을 미래에 패스키로 전환하거나 다른 서비스에서 WebAuthn을 구현할 때 확인할 원칙이다.

### 25.1 서버

- challenge는 충분히 무작위이고 짧은 시간만 유효하게 만든다.
- challenge를 한 번 사용하면 재사용하지 않는다.
- origin과 RP ID를 정확하게 검증한다.
- 공개키, credential ID, user handle, 필요한 메타데이터를 계정과 안전하게 연결한다.
- 사용자 검증이 필요한 정책에서는 UV flag를 검증한다.
- 알고리즘과 credential type을 allowlist 방식으로 검증한다.
- 한 계정에 여러 패스키를 등록할 수 있게 한다.
- 패스키 추가·삭제 시 최근 강한 인증과 사용자 알림을 고려한다.
- 인증 성공 후 세션 보안, CSRF, XSS, 토큰 보호를 별도로 구현한다.

### 25.2 클라이언트와 UX

- `이 기기`, `휴대전화`, `보안 키`, `다른 방법`을 사용자가 이해할 수 있게 표시한다.
- 패스키가 저장될 위치와 동기화 여부를 가능한 범위에서 명확히 한다.
- 취소, 시간 초과, 사용할 패스키 없음, 제공자 잠김을 서로 다른 복구 가능한 상태로 다룬다.
- 여러 계정이 있으면 실제 선택 UI를 제공한다.
- 패스키가 실패해도 계정을 잃지 않도록 안전한 대체 로그인과 복구를 제공한다.
- 공유 기기에 패스키를 만들 때의 위험을 안내한다.
- 사용자가 등록된 패스키의 이름, 생성 시각, 최근 사용, 제거를 관리할 수 있게 한다.

### 25.3 운영과 보안

- 패스키 등록·삭제·복구 이벤트를 감사 가능하게 기록하되 생체 정보나 개인키는 기록하지 않는다.
- 동기화형과 장치 귀속형을 조직 위험도에 맞게 허용한다.
- 관리자·고위험 계정은 예비 하드웨어 키와 더 강한 복구 정책을 고려한다.
- 브라우저, OS, WebView, Electron 버전별 packaged 회귀 테스트를 수행한다.
- 비밀번호 fallback이 남아 있다면 패스키 도입 후에도 그 경로의 피싱·재사용 위험을 계속 관리한다.

## 26. 자주 하는 오해

### `지문이 패스키다`

아니다. 지문은 패스키 개인키 사용을 허용하는 로컬 검증 수단이다.

### `Mac 암호나 Windows PIN을 입력했으니 결국 비밀번호 로그인이다`

웹사이트 비밀번호를 전송하는 것과 다르다. 로컬 기기 잠금을 풀고 개인키 서명을 승인한다.

### `패스키 하나를 모든 사이트에서 쓴다`

아니다. 서비스/RP별로 서로 다른 키 쌍을 사용한다.

### `서버가 패스키를 저장하니 서버가 털리면 바로 로그인할 수 있다`

서버가 보관하는 핵심은 공개키다. 공개키만으로 유효한 로그인 서명을 만들 수 없다. 다만 서버 침해로 계정 연결 정보나 세션, 권한 시스템이 손상될 위험은 여전히 있다.

### `개인키는 어떤 경우에도 기기 밖으로 절대 나가지 않는다`

장치 귀속형에는 맞는 설명이다. 동기화형 패스키는 제공자의 암호화된 동기화 구조를 통해 다른 승인 기기로 복제될 수 있다. RP 서버가 개인키를 받지 않는다는 점은 둘 다 같다.

### `패스키를 쓰면 2단계 인증은 항상 필요 없다`

서비스 정책과 UV 검증에 따라 다르다. 강한 다중 요소 암호 인증으로 사용할 수 있지만 위험 기반 추가 인증이나 조직 정책이 별도 단계를 요구할 수 있다.

### `Windows Hello가 곧 Microsoft 계정 패스키다`

Windows Hello는 플랫폼의 로컬 사용자 검증과 키 보호 체계다. 그 체계로 Microsoft 계정용 패스키뿐 아니라 다른 웹사이트용 패스키를 사용할 수 있다.

### `Safari에서 되면 Electron에서도 반드시 된다`

아니다. 브라우저/앱의 WebAuthn 구현, 플랫폼 인증기 설정, 서명 entitlement, 세션 파티션과 제공자 연동이 다를 수 있다.

### `패스키가 있으면 세션 쿠키는 필요 없다`

대부분의 웹서비스는 패스키로 최초 인증한 뒤 일반적인 세션 쿠키나 토큰을 발급한다. 패스키와 세션 관리는 다른 계층이다.

## 27. 직접 해볼 수 있는 학습 실습

실제 중요한 계정보다 테스트 계정을 사용한다.

### 실습 1: 같은 계정에 서로 다른 저장 방식 등록

1. 테스트 서비스 또는 테스트 Google 계정에 패스키를 만든다.
2. Mac/iPhone의 iCloud Keychain 저장과 FIDO2 보안 키 저장을 각각 비교한다.
3. 계정 보안 설정에서 두 패스키가 별도 항목으로 보이는지 확인한다.
4. 한 패스키를 삭제해도 다른 패스키로 로그인되는지 확인한다.

### 실습 2: 생체 인식과 PIN의 역할 비교

1. Touch ID 또는 Windows Hello 얼굴 인식으로 로그인한다.
2. 같은 패스키에서 PIN이나 기기 암호 fallback을 사용한다.
3. 웹사이트 계정은 같고 로컬 검증 수단만 달라졌음을 확인한다.

### 실습 3: 교차 기기 인증

1. 컴퓨터에서 `다른 기기의 패스키 사용`을 선택한다.
2. 휴대전화로 QR 코드를 스캔한다.
3. Bluetooth를 끈 경우와 켠 경우의 안내를 비교한다.
4. 성공 후 컴퓨터 자격 증명 관리자에 패스키가 새로 저장됐는지 확인한다.

### 실습 4: 피싱 저항성의 구조 확인

실제 피싱 사이트를 만들거나 사용하지 않는다. 대신 브라우저 개발 문서와 WebAuthn 데모에서 RP ID와 origin이 어떻게 표시되는지 확인한다. 다른 도메인이 기존 credential ID를 요청해도 사용할 수 없는 구조를 관찰한다.

### 실습 5: 복구 계획 작성

1. 주 기기를 잃었다고 가정한다.
2. 어떤 보조 기기, 보안 키, 복구 코드로 들어갈지 적는다.
3. 동기화 제공자 계정 자체를 잃었을 때의 복구 경로도 확인한다.
4. 복구 경로가 패스키보다 훨씬 약하지 않은지 검토한다.

## 28. 더 깊이 공부할 때의 순서

1. 이 문서의 1~10장을 읽어 기본 개념과 종류를 구분한다.
2. FIDO Alliance의 [Passkeys 설명](https://fidoalliance.org/passkeys/)으로 공식 용어를 확인한다.
3. [WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/)의 terminology, registration, authentication ceremony를 읽는다.
4. [NIST SP 800-63B-4 authenticator 지침](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/)에서 phishing resistance, replay resistance, authentication intent를 공부한다.
5. [NIST 동기화형 인증기 부록](https://pages.nist.gov/800-63-4/sp800-63b/syncable/)에서 동기화의 보안·복구 trade-off를 읽는다.
6. Apple, Google, Microsoft의 실제 저장·복구 UX를 각각 실습한다.
7. 개발 관점에서는 WebAuthn create/get 요청과 서버 검증을 테스트 환경에서 구현한다.
8. 마지막으로 Electron, WebView, native app처럼 브라우저 밖의 호스트가 WebAuthn을 어떻게 연결하는지 공부한다.

## 29. 용어 사전

| 용어 | 간단한 뜻 |
| --- | --- |
| Passkey | FIDO 표준 기반의 비밀번호 대체 공개키 자격 증명 |
| Credential | 계정 인증에 쓰는 자격 증명 |
| Public key | 서버가 보관하고 서명을 검증하는 키 |
| Private key | 인증기/제공자가 보호하고 서명을 만드는 키 |
| RP | 사용자를 인증하는 웹사이트 또는 서비스 |
| RP ID | 자격 증명이 결합되는 서비스 도메인 식별자 |
| Origin | scheme, host, port로 정해지는 웹 요청 출처 |
| Challenge | 재전송 공격을 막기 위해 서버가 매 요청에 만드는 임의 값 |
| Authenticator | 키 생성, 보호, 서명을 수행하는 장치·구성 요소 |
| Platform authenticator | 현재 기기에 내장된 인증기 |
| Roaming authenticator | 기기 사이를 이동해 쓰는 외부 인증기 |
| Passkey provider | 패스키 생성·보관·동기화·선택을 관리하는 제공자 |
| Discoverable credential | 사용자 이름이나 credential ID 목록 없이 RP 기준으로 계정을 찾을 수 있는 자격 증명 |
| User Presence, UP | 사용자가 터치 등으로 인증 과정에 실제 참여했음을 나타냄 |
| User Verification, UV | PIN·생체 인식 등으로 로컬에서 사용자를 검증했음을 나타냄 |
| Attestation | 등록 시 인증기의 출처·특성을 증명할 수 있는 정보 |
| Assertion | 로그인 시 개인키로 서명해 반환하는 인증 응답 |
| WebAuthn | 웹에서 공개키 자격 증명을 생성·사용하는 W3C API 표준 |
| CTAP | 클라이언트와 외부/교차 기기 인증기 사이의 FIDO 프로토콜 |
| FIDO2 | 일반적으로 WebAuthn과 CTAP을 함께 가리키는 인증 표준 체계 |
| Synced passkey | 제공자를 통해 승인된 여러 기기에 동기화되는 패스키 |
| Device-bound passkey | 특정 기기나 보안 키에 묶여 자동 동기화되지 않는 패스키 |
| Security key | USB/NFC 등으로 사용하는 물리 FIDO 인증기 |
| Windows Hello | Windows의 로컬 사용자 검증 및 보호된 키 사용 체계 |
| Secure Enclave | Apple 기기에서 키와 보안 작업을 보호하는 하드웨어 영역 |
| TPM | Windows PC 등에서 키를 보호하는 Trusted Platform Module |

## 30. 공식 참고 자료

### 표준과 역사

- FIDO Alliance, Passkeys: https://fidoalliance.org/passkeys/
- FIDO Alliance, User Authentication Specifications: https://fidoalliance.org/specifications/
- W3C, Web Authentication Level 3: https://www.w3.org/TR/webauthn-3/
- W3C, 2019 WebAuthn Recommendation 발표: https://www.w3.org/press-releases/2019/webauthn/
- FIDO Alliance, 2013 출범 보도자료: https://fidoalliance.org/assets/downloads/FIDO_Alliance_launch__FINAL__02_12_13docx.pdf
- FIDO Alliance, Multi-Device FIDO Credentials: https://fidoalliance.org/white-paper-multi-device-fido-credentials/
- Apple·Google·Microsoft 2022 공동 발표: https://fidoalliance.org/apple-google-and-microsoft-commit-to-expanded-support-for-fido-standard-to-accelerate-availability-of-passwordless-sign-ins/
- FIDO Credential Exchange Specifications: https://fidoalliance.org/specifications-credential-exchange-specifications/

### 보안 지침

- NIST SP 800-63B-4, Authenticators: https://pages.nist.gov/800-63-4/sp800-63b/authenticators/
- NIST SP 800-63B-4, Syncable Authenticators: https://pages.nist.gov/800-63-4/sp800-63b/syncable/
- NIST SP 800-63B-4 공식 출판 정보: https://www.nist.gov/publications/nist-sp-800-63b-4digital-identity-guidelines-authentication-and-authenticator

### 플랫폼

- Apple Developer, Passkeys: https://developer.apple.com/passkeys/
- Apple Support, Passwords와 iCloud Keychain: https://support.apple.com/en-us/120758
- Google Account Help, 패스키 로그인: https://support.google.com/accounts/answer/13548313
- Microsoft Support, 패스키 생성·저장: https://support.microsoft.com/en-us/windows/synchronize-passkeys-to-your-microsoft-account-be9de83c-6803-4ccc-81f2-e1fcc2fb8110
- Microsoft Learn, Windows 11 Passwordless Sign-in: https://learn.microsoft.com/en-us/windows/security/book/identity-protection-passwordless-sign-in

## 31. 최종 요약

- 패스키는 지문이나 PIN이 아니라 서비스별 공개키·개인키 자격 증명이다.
- 지문, 얼굴, PIN, 기기 암호는 개인키 사용을 승인하는 로컬 검증 수단이다.
- FIDO Alliance의 FIDO2/CTAP과 W3C의 WebAuthn이 기술 기반이다.
- FIDO Alliance는 2012년에 결성되고 2013년에 공개 출범했으며, 2019년 WebAuthn 표준화와 2022년 Apple·Google·Microsoft의 확장 지원을 거쳐 패스키가 대중화됐다.
- 동기화형 패스키와 장치 귀속형 패스키가 있고, 플랫폼 인증기와 로밍 인증기는 별도의 분류 축이다.
- Windows에도 패스키가 있으며 Windows Hello, 동기화 관리자, 휴대전화, FIDO2 보안 키를 사용할 수 있다.
- 패스키는 피싱, 비밀번호 재사용, 크리덴셜 스터핑, replay 위험을 크게 줄이지만 세션 탈취, 악성코드, 약한 계정 복구, 잘못된 권한 부여까지 해결하지는 않는다.
- 패스키 인증이 끝난 뒤에도 웹서비스는 보통 세션 쿠키를 사용한다. Clipper Studio의 yt-dlp 경로도 패스키 자체가 아니라 Google 로그인 후의 YouTube 세션 쿠키를 사용한다.
- Safari나 Chrome에서 패스키가 된다고 Electron 내장 창에서도 자동으로 되는 것은 아니다. 호스트의 WebAuthn 구현, OS 연동, 앱 서명·entitlement, 세션과 packaged QA가 필요하다.
