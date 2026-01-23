#!/usr/bin/env python3
"""
Skillthon 이름표 생성 스크립트
Echo & Delta와 동일한 사이즈/형식, Anthropic 후원
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 디렉토리 설정
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent  # 3-skillthon/
OUTPUT_DIR = BASE_DIR / "assets" / "nametags"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 이미지 에셋
ASSETS_DIR = BASE_DIR / "assets"
QR_CODE_PATH = ASSETS_DIR / "webpage-qr.png"
ANTHROPIC_LOGO_PATH = ASSETS_DIR / "Anthropic_Logo_1.png"
ROCKET_ICON_PATH = ASSETS_DIR / "rocket_icon.png"

# 이름표 사이즈 (Echo & Delta와 동일)
WIDTH = 718   # 359 * 2 for high resolution
HEIGHT = 922  # 461 * 2 for high resolution

# 색상
BG_COLOR = (240, 239, 234)  # #F0EFEA
WHITE = (255, 255, 255)
DARK_TEXT = (33, 33, 33)
MEDIUM_TEXT = (100, 100, 100)
LIGHT_TEXT = (150, 150, 150)
GRAY = (209, 213, 220)


def get_font(size: int, bold: bool = False):
    """시스템 폰트 로드"""
    font_paths = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    return ImageFont.load_default()


def draw_rounded_rectangle(draw, xy, radius, fill):
    """둥근 모서리 사각형 그리기"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill)
    draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill)


def create_nametag(name: str, team: str, role: str, index: int,
                   qr_img: Image.Image, anthropic_img: Image.Image):
    """이름표 이미지 생성 - Echo & Delta 레이아웃 기반"""
    SCALE = 2

    # 이미지 생성
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 배경 장식 원 (반투명 효과)
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse([590, -128, 590 + 256, -128 + 256], fill=(0, 0, 0, 8))
    overlay_draw.ellipse([-96, 826, -96 + 192, 826 + 192], fill=(0, 0, 0, 8))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # 폰트
    title_font = get_font(60)
    subtitle_font = get_font(36)
    label_font = get_font(20)

    # AI Builders Meetup
    title = "AI Builders Meetup"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((WIDTH - title_width) / 2, 80), title, font=title_font, fill=DARK_TEXT)

    # Skillthon
    subtitle = "Skillthon"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((WIDTH - subtitle_width) / 2, 154), subtitle, font=subtitle_font, fill=DARK_TEXT)

    # by Team Attention
    byline = "by Team Attention"
    byline_bbox = draw.textbbox((0, 0), byline, font=subtitle_font)
    byline_width = byline_bbox[2] - byline_bbox[0]
    draw.text(((WIDTH - byline_width) / 2, 196), byline, font=subtitle_font, fill=MEDIUM_TEXT)

    # QR 코드 박스
    qr_box_x, qr_box_y = 62, 308
    qr_box_size = 132
    draw_rounded_rectangle(draw, [qr_box_x, qr_box_y, qr_box_x + qr_box_size, qr_box_y + qr_box_size], 20, WHITE)
    qr_resized = qr_img.resize((113, 113), Image.Resampling.LANCZOS)
    img.paste(qr_resized, (72, 318))

    # "밋업 안내" 라벨
    label = "밋업 안내"
    label_bbox = draw.textbbox((0, 0), label, font=label_font)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text((127 - label_width / 2, 454), label, font=label_font, fill=MEDIUM_TEXT)

    # Anthropic 로고 박스
    logo_box_x, logo_box_y = 230, 308
    logo_box_w, logo_box_h = 452, 132
    draw_rounded_rectangle(draw, [logo_box_x, logo_box_y, logo_box_x + logo_box_w, logo_box_y + logo_box_h], 20, WHITE)
    # Anthropic 로고 (800x90) - 박스 내부에 맞게 리사이즈
    logo_max_w = logo_box_w - 48
    logo_max_h = logo_box_h - 44
    logo_ratio = min(logo_max_w / anthropic_img.width, logo_max_h / anthropic_img.height)
    logo_w = int(anthropic_img.width * logo_ratio)
    logo_h = int(anthropic_img.height * logo_ratio)
    logo_resized = anthropic_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    logo_x = logo_box_x + (logo_box_w - logo_w) // 2
    logo_y = logo_box_y + (logo_box_h - logo_h) // 2
    img.paste(logo_resized, (logo_x, logo_y), logo_resized if logo_resized.mode == 'RGBA' else None)

    # "Sponsor" 라벨
    sponsor_label = "Sponsor"
    sponsor_bbox = draw.textbbox((0, 0), sponsor_label, font=label_font)
    sponsor_width = sponsor_bbox[2] - sponsor_bbox[0]
    draw.text((455 - sponsor_width / 2, 456), sponsor_label, font=label_font, fill=MEDIUM_TEXT)

    # 이름/팀 흰색 박스
    name_box_x, name_box_y = 48, 558
    name_box_w, name_box_h = 622, 408
    draw_rounded_rectangle(draw, [name_box_x, name_box_y, name_box_x + name_box_w, name_box_y + name_box_h], 20, WHITE)

    # 역할 태그 (있는 경우)
    role_offset = 0
    if role:
        role_colors = {
            "Host": (220, 50, 50),
            "Speaker": (50, 100, 220),
            "Staff": (34, 160, 80),
        }
        role_color = role_colors.get(role, MEDIUM_TEXT)
        role_font = get_font(24)
        role_text = f"[ {role} ]"
        role_bbox = draw.textbbox((0, 0), role_text, font=role_font)
        role_width = role_bbox[2] - role_bbox[0]
        draw.text(((WIDTH - role_width) / 2, 578), role_text, font=role_font, fill=role_color)
        role_offset = 36

    # 이름 텍스트
    name_font = get_font(56)
    name_bbox = draw.textbbox((0, 0), name, font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    name_height = name_bbox[3] - name_bbox[1]
    name_x = (WIDTH - name_width) / 2
    name_underline_y = 558 + 48 + 130 + role_offset
    draw.text((name_x, name_underline_y - name_height - 20), name, font=name_font, fill=(0, 0, 0))

    # 이름 아래 밑줄
    draw.line([96, name_underline_y, 622, name_underline_y], fill=GRAY, width=4)

    # 팀명
    org_font = get_font(32)
    org_underline_y = name_underline_y + 40 + 76
    if team:
        org_bbox = draw.textbbox((0, 0), team, font=org_font)
        org_width = org_bbox[2] - org_bbox[0]
        org_height = org_bbox[3] - org_bbox[1]
        org_x = (WIDTH - org_width) / 2
        draw.text((org_x, org_underline_y - org_height - 16), team, font=org_font, fill=MEDIUM_TEXT)

    # 팀명 아래 밑줄
    draw.line([96, org_underline_y, 622, org_underline_y], fill=GRAY, width=4)

    # 파일 저장
    safe_name = name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
    filename = f"{index:02d}_{safe_name}.png"
    filepath = OUTPUT_DIR / filename
    img.save(filepath, "PNG", quality=95)
    print(f"생성됨: {filename}")
    return filepath


def get_participants():
    """참가자 목록"""
    teams = [
        {"name": "정승현", "team": "코드스쿼드", "role": ""},
        {"name": "문현경", "team": "코드스쿼드", "role": ""},
        {"name": "김보겸", "team": "코드스쿼드", "role": ""},
        {"name": "홍남호", "team": "오프라이트", "role": ""},
        {"name": "여한우리", "team": "오프라이트", "role": ""},
        {"name": "조쉬(김승권)", "team": "Million Agents", "role": ""},
        {"name": "서인근", "team": "Million Agents", "role": ""},
        {"name": "박종현", "team": "수도노토기릿", "role": ""},
        {"name": "변형호", "team": "수도노토기릿", "role": ""},
        {"name": "이지윤", "team": "수도노토기릿", "role": ""},
        {"name": "송범근", "team": "Grow3", "role": ""},
        {"name": "조민규", "team": "Grow3", "role": ""},
        {"name": "강주혁", "team": "Grow3", "role": ""},
        {"name": "김서진", "team": "랜덤 1조", "role": ""},
        {"name": "장원준", "team": "랜덤 1조", "role": ""},
        {"name": "최훈민", "team": "랜덤 1조", "role": ""},
        {"name": "이승민", "team": "랜덤 2조", "role": ""},
        {"name": "이재준", "team": "랜덤 2조", "role": ""},
        {"name": "공지훈", "team": "랜덤 2조", "role": ""},
        {"name": "이분도", "team": "랜덤 2조", "role": ""},
        {"name": "최소혜", "team": "랜덤 3조", "role": ""},
        {"name": "이예찬", "team": "랜덤 3조", "role": ""},
        {"name": "김윤서", "team": "랜덤 3조", "role": ""},
        {"name": "김동언", "team": "랜덤 3조", "role": ""},
    ]

    staff = [
        {"name": "정구봉", "team": "Team Attention", "role": "Host"},
        {"name": "박건태", "team": "Team Attention", "role": "Host"},
        {"name": "이호연", "team": "Team Attention", "role": "Host"},
        {"name": "김창회", "team": "Team Attention", "role": "Host"},
        {"name": "이엽", "team": "Anthropic", "role": "Speaker"},
        {"name": "최종원", "team": "딜라이트룸", "role": "Speaker"},
        {"name": "이재규", "team": "ZEP", "role": "Speaker"},
        {"name": "김연규", "team": "Indent", "role": "Speaker"},
    ]

    return teams + staff


def create_pdf(nametag_paths: list):
    """이름표 4장씩 A4 페이지에 배치한 PDF 생성"""
    # A4 at 300 DPI
    A4_W, A4_H = 2480, 3508
    MARGIN = 40
    COLS, ROWS = 2, 2

    cell_w = (A4_W - MARGIN * 3) // COLS
    cell_h = (A4_H - MARGIN * 3) // ROWS

    pages = []
    for page_start in range(0, len(nametag_paths), 4):
        page_imgs = nametag_paths[page_start:page_start + 4]
        page = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))

        for idx, img_path in enumerate(page_imgs):
            col = idx % COLS
            row = idx // COLS

            nametag = Image.open(img_path)
            # 셀에 맞게 스케일 (비율 유지)
            ratio = min(cell_w / nametag.width, cell_h / nametag.height)
            new_w = int(nametag.width * ratio)
            new_h = int(nametag.height * ratio)
            nametag_resized = nametag.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # 셀 내 중앙 배치
            x = MARGIN + col * (cell_w + MARGIN) + (cell_w - new_w) // 2
            y = MARGIN + row * (cell_h + MARGIN) + (cell_h - new_h) // 2
            page.paste(nametag_resized, (x, y))

        pages.append(page)

    pdf_path = OUTPUT_DIR / "nametags_print.pdf"
    if pages:
        pages[0].save(pdf_path, "PDF", save_all=True, append_images=pages[1:], resolution=300)
    print(f"\nPDF 생성: {pdf_path} ({len(pages)}페이지)")
    return pdf_path


def main():
    participants = get_participants()
    print(f"총 {len(participants)}명의 이름표 생성")
    print(f"저장 위치: {OUTPUT_DIR}\n")

    # 에셋 이미지 로드
    qr_img = Image.open(QR_CODE_PATH).convert('RGBA')
    anthropic_img = Image.open(ANTHROPIC_LOGO_PATH).convert('RGBA')
    print(f"  - QR 코드: {QR_CODE_PATH}")
    print(f"  - Anthropic 로고: {ANTHROPIC_LOGO_PATH}\n")

    nametag_paths = []
    for i, p in enumerate(participants, 1):
        path = create_nametag(p["name"], p["team"], p["role"], i, qr_img, anthropic_img)
        nametag_paths.append(path)

    print(f"\n완료! {len(participants)}개의 이름표가 생성되었습니다.")
    print(f"저장 위치: {OUTPUT_DIR}")

    # PDF 생성
    create_pdf(nametag_paths)


if __name__ == "__main__":
    main()
