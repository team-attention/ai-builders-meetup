# AI Builders Meetup

## 프로젝트 구조

회차별 디렉토리 패턴:
- `{N}-{codename}/` - N회차 밋업 (예: `2-echo-delta`)
  - `slides/` - 발표자료 PDF
  - `videos/raw/` - 원본 영상
  - `videos/subtitles/` - 자막 (raw/, corrected/, en/)
  - `terms/` - 용어집

스크립트: `.claude/skills/video-subtitle/scripts/`, `.claude/skills/youtube-upload/scripts/`

Skills/Agents는 `.claude/` 아래에 있음. 상세 구조는 필요 시 탐색.

## 영상-PDF 매칭 (2회차)

| 영상 | 발표자료 |
|------|----------|
| 서진님 발표 | `slides/1-김서진-[251230] AI-Native Company.pdf` |
| 동훈님 발표 | `slides/2-이동훈-myrealtrip-donghoon-ailab.pdf` |
| 동운님 발표 | `slides/3-최동운-계산기 압수 당해서...pdf` |
| 건호님 발표 | `slides/4-신건호-AI Builder Meetup...pdf` |
| 키노트 | `slides/0-정구봉-echo-delta-keynote.pdf` |
| 패널 토론 | `terms/glossary.yaml` (통합 용어집) |

## 자주 쓰는 스킬

| 스킬 | 용도 |
|------|------|
| `/video-subtitle` | 자막 생성/교정 |
| `/finalize` | 영어 번역 + 번인 |
| `/youtube-upload` | 유튜브 업로드 |
| `/create-pr` | PR 생성 |
| `/clarify` | 요구사항 구체화 |

## 주의사항

1. **한글 파일명**: macOS/WSL에서 NFD 형식으로 저장됨. 반드시 NFC 정규화 후 비교:
   ```python
   import unicodedata
   filename = unicodedata.normalize('NFC', filename)
   ```
