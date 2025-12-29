# AI Builders Meetup 이름표 생성기 - Human-AI 협업 스토리

> Claude Code와 인간이 협력하여 Figma 디자인부터 실제 프린팅까지 완성한 과정

---

## 1. Figma 연동: 디자인에서 코드로

**시작점**: Figma URL 하나와 참석자 CSV 파일

```
https://www.figma.com/design/gaJjcTioflot5HUyKHtrhy/meetup-02-목걸이?node-id=1-3
```

Claude Code가 Figma MCP를 통해:
- 디자인 컨텍스트 추출 (좌표, 색상, 폰트 크기)
- QR 코드, Socar 로고 등 이미지 에셋 다운로드
- 정확한 레이아웃 수치를 Python 스크립트로 변환

**결과**: Figma 디자인과 픽셀 단위로 일치하는 이름표 템플릿 구현

---

## 2. 자동화: 56명의 이름표 일괄 생성

CSV 파일에서 참석자 정보를 읽어 자동 생성:

| 구분 | 처리 방식 |
|------|----------|
| 일반 게스트 | 이름 + 소속 |
| 호스트 | `[Host] 이름` + 소속 |
| 스피커 | `[Speaker] 이름` + 소속 |
| 소속 미입력 | 🚀 아이콘 + "Stealth" |

```python
# 56개 이름표 자동 생성
for attendee in attendees:
    create_nametag(name, organization, ...)
```

---

## 3. 창의적 문제 해결: 로켓 아이콘 직접 디자인

**문제**: Pillow에서 이모지(🚀) 렌더링 불가

**시도한 방법들**:
1. Apple Color Emoji 폰트 → 실패
2. 이모지 별도 렌더링 → 실패

**해결책**: Pillow로 로켓 아이콘 직접 그리기

```python
# 로켓 본체 (삼각형 + 직사각형)
draw.polygon([(32, 4), (20, 24), (44, 24)], fill=color)  # 머리
draw.rectangle([22, 24, 42, 48], fill=color)              # 몸체
draw.polygon([(26, 48), (32, 60), (38, 48)], fill=(255, 100, 50))  # 불꽃
```

---

## 4. Human-AI 협업: 색상 보정 반복 테스트

**문제**: 화면의 선명한 파란색(#0078FF)이 잉크젯 출력 시 탁하게 나옴

**원인**: RGB(모니터) → CMYK(프린터) 색역 차이

**협업 과정**:

| 버전 | 보정값 | 인간 피드백 |
|------|--------|------------|
| v1 (원본) | - | "탁해" |
| bright | 채도 +20%, 밝기 +10% | "아직 탁해" |
| bright (update) | 채도 +40%, 밝기 +20% | "아직 부족해" |
| bright_v2 | 채도 +60%, 밝기 +30% | "좋았어!" ✅ |

```python
# 최종 역보정 설정
enhancer = ImageEnhance.Color(img)
img = enhancer.enhance(1.6)  # 채도 +60%

enhancer = ImageEnhance.Brightness(img)
img = enhancer.enhance(1.3)  # 밝기 +30%
```

---

## 5. 마지막 터치: AI가 직접 프린터로 출력

```bash
# Claude Code가 실행한 명령
lpr -o media=A4 -o fit-to-page nametags_blank.pdf
```

AI가 프린터에 직접 출력 명령을 보내고, 인간이 결과물을 검토하는 협업 완성.

---

## 생성된 파일들

| 파일 | 설명 |
|------|------|
| `nametags/` | 56개 개별 이름표 PNG |
| `nametags_print.pdf` | 원본 RGB PDF (4개/페이지) |
| `nametags_print_cmyk.pdf` | CMYK 변환 PDF |
| `nametags_print_bright.pdf` | 역보정 v1 |
| `nametags_print_bright_v2.pdf` | 역보정 v2 (최종) |
| `nametags_blank.pdf` | 빈 이름표 (여유분) |
| `generate_nametags.py` | 이름표 생성 스크립트 |
| `rocket_icon.png` | 직접 디자인한 로켓 아이콘 |

---

## 핵심 인사이트

1. **End-to-End 자동화**: 디자인 → 코드 → 데이터 처리 → 인쇄까지 하나의 흐름
2. **창의적 우회**: 기술적 한계(이모지 렌더링)를 직접 그리기로 해결
3. **반복적 협업**: 색상 보정처럼 정답이 없는 문제는 인간 피드백 + AI 실행의 반복으로 해결
4. **물리 세계 연결**: AI가 디지털 작업을 넘어 실제 프린터 출력까지 수행

---

*2024년 12월 28일, AI Builders Meetup Echo & Delta 준비 중*
