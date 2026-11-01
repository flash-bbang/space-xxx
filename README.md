# SPACE XXX

블록 쌓다가 비둘기 똥 맞고, UFO한테 털리고, 120층 찍으면 랜덤 점수만큼 우주로 날아가는 병맛 탑 쌓기 게임.

파일은 `index.html` 하나뿐입니다. 이미지, 음원, 빌드 과정이 필요 없어요.

---

## 1. GitHub Pages에 올리기

1. GitHub에서 새 저장소를 만듭니다 (예: `space-xxx`). **Public**으로 만들어야 무료로 Pages를 쓸 수 있어요.
2. `index.html`과 이 `README.md`를 저장소 맨 위(루트)에 업로드합니다.
   - 저장소 화면의 **Add file → Upload files**로 끌어다 놓으면 됩니다.
3. 저장소의 **Settings → Pages**로 갑니다.
4. **Source**를 `Deploy from a branch`, 브랜치를 `main`, 폴더를 `/ (root)`로 고르고 저장합니다.
5. 1~2분 뒤 `https://내아이디.github.io/space-xxx/` 주소로 게임이 열립니다.

이 상태에서도 닉네임, 순위, 기록 공유가 모두 동작해요. 다만 순위는 **각자 자기 기기에 남긴 기록만** 보입니다.
친구들과 같은 순위표를 보려면 아래 2번을 해주세요.

---

## 2. 온라인 순위 켜기 (Firebase, 무료로 시작 가능)

GitHub Pages는 파일만 보여주는 곳이라 다른 사람의 기록을 저장할 수 없어요.
그래서 기록을 저장할 곳으로 Google의 Firebase(Firestore)를 씁니다. 서버 코드를 짤 필요는 없고, 설정만 하면 됩니다.

### 2-1. Firebase 프로젝트와 데이터베이스 만들기

1. <https://console.firebase.google.com> 에 Google 계정으로 들어가 **프로젝트 추가**를 누릅니다.
   - 이름은 아무거나 (예: `space-xxx`). Google 애널리틱스는 꺼도 됩니다.
2. 왼쪽 메뉴에서 **Firestore Database → 데이터베이스 만들기**를 누릅니다.
   - 위치는 한국 사용자라면 `asia-northeast3 (서울)`을 추천합니다.
   - **프로덕션 모드**로 시작합니다.

### 2-2. 보안 규칙 넣기

Firestore 화면의 **규칙** 탭에 아래 내용을 통째로 붙여넣고 **게시**합니다.
누구나 순위를 읽을 수 있고, 정해진 형식의 기록만 새로 추가할 수 있으며, 수정·삭제는 막습니다.

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /scores/{id} {
      allow read: if true;
      allow create: if request.resource.data.keys().hasOnly(['name', 'score', 'floors', 'dest', 'ts'])
        && request.resource.data.name is string
        && request.resource.data.name.size() >= 1
        && request.resource.data.name.size() <= 12
        && request.resource.data.score is int
        && request.resource.data.score >= 1
        && request.resource.data.score <= 20120
        && request.resource.data.floors is int
        && request.resource.data.floors >= 0
        && request.resource.data.floors <= 120
        && request.resource.data.dest is string
        && request.resource.data.dest.size() <= 12
        && request.resource.data.ts is timestamp;
      allow update, delete: if false;
    }
  }
}
```

점수 상한 `20120`은 120층 + 블랙홀 최대 보너스 19,999점에서 나온 값이에요.

### 2-3. 프로젝트 ID와 API 키 복사

1. 왼쪽 위 톱니바퀴 → **프로젝트 설정**으로 갑니다.
2. **내 앱**에서 웹 아이콘 `</>`을 눌러 웹 앱을 하나 등록합니다 (호스팅 설정은 체크하지 않아도 됩니다).
3. 화면에 나오는 설정 코드에서 `projectId`와 `apiKey` 값을 복사합니다.

### 2-4. index.html에 붙여넣기

`index.html`에서 아래 줄을 찾아 값을 채운 뒤 GitHub에 다시 올립니다.

```js
const LEADERBOARD = { projectId: '', apiKey: '' };
```

예시:

```js
const LEADERBOARD = { projectId: 'space-xxx-12345', apiKey: 'AIzaSy...' };
```

GitHub 웹에서 `index.html`을 열고 연필 아이콘으로 바로 고쳐도 됩니다. 저장(커밋)하면 1~2분 뒤 반영돼요.

이제 순위 화면 안내 문구가 **"전체 TOP 30"** 으로 바뀌고, 모든 플레이어가 같은 순위표를 봅니다.

---

## 알아두면 좋은 점

- **API 키가 공개돼도 괜찮나요?** Firebase 웹 API 키는 원래 브라우저에 노출되는 값이고, 데이터는 위의 보안 규칙이 지킵니다. 더 안전하게 하려면 Google Cloud 콘솔의 **API 및 서비스 → 사용자 인증 정보**에서 이 키를 `내아이디.github.io` 주소에서만 쓰도록 제한하세요.
- **점수 조작:** 브라우저에서 돌아가는 게임이라 마음먹은 사람이 가짜 점수를 보내는 것을 완전히 막을 수는 없어요. 규칙으로 말이 안 되는 점수는 거르고, 이상한 기록은 Firestore 콘솔의 `scores` 컬렉션에서 직접 지우면 됩니다.
- **도배 방지:** 한 기기에서는 자기 최고 점수를 넘었을 때만 기록이 올라갑니다.
- **닉네임:** 최대 12자이고, 입력해야 게임을 시작할 수 있어요. 욕설 필터는 없으니, 문제가 되는 닉네임은 콘솔에서 지워주세요.
- **비용:** Firebase는 무료 요금제로 시작할 수 있어요. 사용량이 크게 늘면 Firebase 콘솔의 사용량 화면을 확인하세요.
