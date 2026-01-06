---
name: youtube-upload
description: |
  영상을 유튜브에 업로드하고 자막/제목/설명을 자동 설정하는 스킬.
  "유튜브 업로드", "영상 업로드", "YouTube" 요청에 사용.
  발표자료(PDF) + 자막(SRT)을 참조하여 제목/설명 자동 생성.
arguments:
  - name: video
    description: 업로드할 영상 파일 경로 (필수)
    required: true
  - name: subtitle
    description: 자막 파일 경로 (영어 SRT, 선택)
    required: false
  - name: reference
    description: 발표자료(PDF) 경로 (제목/설명 생성용, 선택)
    required: false
  - name: privacy
    description: 공개 설정 (private/unlisted/public, 기본값 private)
    required: false
  - name: title
    description: 영상 제목 (미지정 시 자동 생성)
    required: false
  - name: description
    description: 영상 설명 (미지정 시 자동 생성)
    required: false
---

# YouTube Upload Skill

영상을 유튜브에 업로드하고 메타데이터를 설정하는 스킬.

## 사용법

```bash
# 기본 업로드 (private)
/youtube-upload --video /path/to/video.mp4

# 자막 포함 업로드
/youtube-upload --video /path/to/video.mp4 --subtitle /path/to/subtitle_en.srt

# 발표자료 기반 제목/설명 자동 생성
/youtube-upload --video /path/to/video.mp4 --subtitle /path/to/subtitle_en.srt --reference /path/to/slides.pdf

# 공개 설정 변경
/youtube-upload --video /path/to/video.mp4 --privacy unlisted

# 제목/설명 직접 지정
/youtube-upload --video /path/to/video.mp4 --title "발표 제목" --description "설명"
```

## 워크플로우

```
┌─────────────────────────────────────────────────────┐
│                  Step 0: 인증 확인                   │
│  OAuth 토큰 확인 → 없으면 인증 안내                   │
└────────┬────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────┐
│                  Step 1: 입력 검증                   │
│  영상 존재 확인, 자막/발표자료 확인                    │
└────────┬────────────────────────────────────────────┘
         ▼
┌─────────────────┐
│ metadata-       │  발표자료 + 자막 참조하여
│ generator       │  제목/설명 생성
└────────┬────────┘  [title/description 미지정 시만]
         ▼
┌─────────────────┐
│ youtube-        │  영상 업로드 + 자막 추가
│ uploader        │  → 유튜브 URL 반환
└────────┬────────┘
         ▼
┌─────────────────┐
│  결과 보고서     │  URL, 메타데이터 정보 출력
└─────────────────┘
```

## 실행 단계

### Step 0: 인증 확인

OAuth 토큰 파일 존재 확인:

```bash
python scripts/youtube/auth.py --check
```

토큰 없으면 인증 안내:
```
YouTube API 인증이 필요합니다.

1. Google Cloud Console에서 OAuth 클라이언트 ID 생성:
   https://console.cloud.google.com/apis/credentials

2. 다운로드한 client_secrets.json을 프로젝트 루트에 저장

3. 인증 실행:
   python scripts/youtube/auth.py

4. 브라우저에서 계정 선택 및 권한 허용
```

### Step 1: 입력 검증

파일 존재 확인:
- `--video`: 필수, 파일 존재 확인
- `--subtitle`: 선택, 있으면 파일 존재 확인
- `--reference`: 선택, 있으면 파일 존재 확인

### Step 2: 메타데이터 생성 (metadata-generator)

`--title` 또는 `--description` 미지정 시:

```
Task: youtube-upload:metadata-generator
Prompt: |
  다음 자료를 참조하여 유튜브 영상의 제목과 설명을 생성해주세요.
  - video_path: $video
  - reference_path: $reference (있으면)
  - subtitle_path: $subtitle (있으면)
```

### Step 3: 영상 업로드 (youtube-uploader)

```
Task: youtube-upload:youtube-uploader
Prompt: |
  다음 영상을 유튜브에 업로드해주세요.
  - video_path: $video
  - title: $title (또는 생성된 제목)
  - description: $description (또는 생성된 설명)
  - privacy: $privacy (기본값: private)
  - subtitle_path: $subtitle (있으면)
```

### Step 4: 결과 보고

```markdown
## 유튜브 업로드 완료

- **영상**: {video_filename}
- **URL**: https://youtu.be/{video_id}
- **공개설정**: {privacy}

### 메타데이터
- **제목**: {title}
- **설명**: {description 첫 100자}...

### 자막
- **파일**: {subtitle_filename}
- **언어**: 영어

### 다음 단계
- 영상 확인: {url}
- 공개 설정 변경: YouTube Studio에서 수정
```

## 시스템 요구사항

### 환경
- Python 3.10+
- Google Cloud 프로젝트 (YouTube Data API v3 활성화)
- OAuth 클라이언트 ID (데스크톱 앱 유형)

### 필요 패키지
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### API 할당량
- 영상 업로드: 1600 유닛/건
- 자막 업로드: 400 유닛/건
- 일일 기본 할당량: 10,000 유닛

## OAuth 설정 가이드

### 1. Google Cloud Console 프로젝트

1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택

### 2. YouTube Data API v3 활성화

1. APIs & Services > Library
2. "YouTube Data API v3" 검색 및 활성화

### 3. OAuth 동의 화면 설정

1. APIs & Services > OAuth consent screen
2. User Type: External
3. 앱 이름, 사용자 지원 이메일 입력
4. Scopes: `youtube.upload`, `youtube.force-ssl` 추가
5. Test users에 본인 이메일 추가

### 4. OAuth 클라이언트 ID 생성

1. APIs & Services > Credentials
2. Create Credentials > OAuth client ID
3. Application type: Desktop app
4. 이름 입력 후 Create
5. JSON 다운로드 → `client_secrets.json`으로 저장 (프로젝트 루트)

### 5. 인증 실행

```bash
python scripts/youtube/auth.py
```

브라우저에서 계정 선택 및 권한 허용 → `.youtube_token.json` 자동 생성

## 보안 주의사항

1. `client_secrets.json`은 절대 커밋하지 않음 (.gitignore에 포함)
2. `.youtube_token.json`도 절대 커밋하지 않음 (.gitignore에 포함)
3. 업로드 기본값은 항상 `private`

## 예시

### 예시 1: 밋업 영상 업로드

```bash
# burnin 영상 (한국어 자막 하드코딩) + 영어 자막 (YouTube 자막 트랙)
/youtube-upload \
  --video 2-echo-delta/videos/burnin_output/meetup_02_서진님_burnin.mp4 \
  --subtitle 2-echo-delta/videos/subtitles/en/meetup_02_서진님_corrected_en.srt \
  --reference 2-echo-delta/slides/1-김서진-AI-Native.pdf
```

**업로드 구조**:
- 한국어 자막: 영상에 하드코딩 (항상 표시)
- 영어 자막: YouTube 자막 트랙 (시청자가 선택)

### 출력

```
## 유튜브 업로드 완료

- **영상**: meetup_02_서진님_burnin.mp4
- **URL**: https://youtu.be/abc123xyz
- **공개설정**: private

### 메타데이터
- **제목**: [AI Builders Meetup #2] AI-Native Company 구축 전략 - 김서진
- **설명**: AI-Native Company를 구축하기 위한 전략과 실제 사례를 공유합니다...

### 자막
- **한국어**: 영상에 하드코딩됨
- **영어**: meetup_02_서진님_corrected_en.srt (YouTube 자막)

### 다음 단계
- 영상 확인: https://youtu.be/abc123xyz
- 공개 설정 변경: YouTube Studio에서 수정
```
