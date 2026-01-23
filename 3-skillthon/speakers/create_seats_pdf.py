#!/usr/bin/env python3
"""Skillthon Seats 명패 PDF 생성

A4를 가로로 4등분해서 접어 사용하는 명패 (테이블 텐트)
- 섹션 2: 앞면 텍스트 (정방향)
- 섹션 3: 뒷면 텍스트 (뒤집힘)

생성물:
1. speaker-seats.pdf - 스피커용 명패
2. team-seats.pdf - 팀별 명패 (각 팀 이름으로 한 페이지씩)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

# 한글 폰트 등록
FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
pdfmetrics.registerFont(TTFont("AppleGothic", FONT_PATH))

# A4: 210mm x 297mm
WIDTH, HEIGHT = A4
SECTION_HEIGHT = HEIGHT / 4

# 출력 경로
OUTPUT_DIR = Path(__file__).parent

# 팀 목록
TEAMS = [
    "코드스쿼드",
    "오프라이트",
    "Million Agents",
    "수도노토기릿",
    "그로스리 (Grow3)",
    "랜덤 1조",
    "랜덤 2조",
    "랜덤 3조",
]


def draw_page(c, text, font_name="Helvetica-Bold", font_size=48):
    """한 페이지에 테이블 텐트 명패를 그린다."""
    # 접는 선 그리기 (점선)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setDash(3, 3)
    for i in range(1, 4):
        y = i * SECTION_HEIGHT
        c.line(10 * mm, y, WIDTH - 10 * mm, y)

    c.setDash()  # 점선 해제

    # 텍스트 설정
    c.setFont(font_name, font_size)
    c.setFillColorRGB(0.1, 0.1, 0.1)

    # 텍스트 너비 계산
    text_width = c.stringWidth(text, font_name, font_size)

    # 페이지 너비에 맞게 폰트 크기 조정
    max_width = WIDTH - 40 * mm
    if text_width > max_width:
        font_size = font_size * max_width / text_width
        c.setFont(font_name, font_size)
        text_width = c.stringWidth(text, font_name, font_size)

    # 섹션 2: 앞면 (정방향) - 아래에서 2번째 섹션
    section2_center_y = SECTION_HEIGHT * 1.5
    c.drawString((WIDTH - text_width) / 2, section2_center_y - font_size / 3, text)

    # 섹션 3: 뒷면 (뒤집힘) - 아래에서 3번째 섹션
    section3_center_y = SECTION_HEIGHT * 2.5
    c.saveState()
    c.translate(WIDTH / 2, section3_center_y)
    c.rotate(180)
    c.drawString(-text_width / 2, -font_size / 3, text)
    c.restoreState()

    # 접는 방법 안내 (맨 위 섹션에 작게)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(
        15 * mm, HEIGHT - 15 * mm, "↓ Fold along the dotted lines to create a table tent"
    )


def create_speaker_seats():
    """Speaker Seats PDF 생성"""
    output_path = OUTPUT_DIR / "speaker-seats.pdf"
    c = canvas.Canvas(str(output_path), pagesize=A4)
    draw_page(c, "Speaker Seats", font_name="Helvetica-Bold", font_size=48)
    c.save()
    print(f"Speaker seats PDF 생성 완료: {output_path}")


def create_team_seats():
    """팀별 Seats PDF 생성 (모든 팀을 한 PDF에)"""
    output_path = OUTPUT_DIR / "team-seats.pdf"
    c = canvas.Canvas(str(output_path), pagesize=A4)

    for i, team_name in enumerate(TEAMS):
        # 한글이 포함된 팀명은 AppleGothic 사용
        has_korean = any("\uac00" <= ch <= "\ud7a3" for ch in team_name)
        font_name = "AppleGothic" if has_korean else "Helvetica-Bold"
        draw_page(c, team_name, font_name=font_name, font_size=48)
        if i < len(TEAMS) - 1:
            c.showPage()

    c.save()
    print(f"Team seats PDF 생성 완료: {output_path}")


if __name__ == "__main__":
    create_speaker_seats()
    create_team_seats()
