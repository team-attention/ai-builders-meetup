#!/usr/bin/env python3
"""
Subtitle Corrector - Step 3 of subtitle generation pipeline
Corrects technical terminology using reference PDF
Customized for 건호님's AX/B2B presentation
"""
import sys
import os
import re
import unicodedata

def parse_srt(content):
    """Parse SRT content into list of segments"""
    blocks = content.strip().split("\n\n")
    segments = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                timestamp = lines[1]
                text = "\n".join(lines[2:])
                segments.append({
                    'index': index,
                    'timestamp': timestamp,
                    'text': text
                })
            except (ValueError, IndexError):
                continue

    return segments

def extract_keywords_from_pdf(pdf_path):
    """
    Extract technical terms from 건호님's B2B/AX presentation
    Based on PDF content analysis
    """
    # Terms specific to 건호님's presentation about AX (AI Transformation)
    presentation_specific_terms = {
        # Core concepts from the presentation
        "AX": ["에이엑스", "에이 엑스", "에이X"],
        "AI Transformation": ["에이아이 트랜스포메이션", "에이아이 트랜스 포메이션"],
        "B2B": ["비투비", "비 투 비", "비트비"],
        "DAY1COMPANY": ["데이원컴퍼니", "데이 원 컴퍼니", "데이1컴퍼니"],
        "doeat": ["두잇", "두 잇", "도잇"],
        "KEARNEY": ["커니", "컨설팅"],
        "KAIST": ["카이스트", "카 이스트"],

        # Key presentation terms
        "PMF": ["피엠에프", "피 엠 에프"],
        "MVP": ["엠브이피", "엠 브이 피"],
        "PoC": ["포씨", "피오씨", "피오 씨"],
        "ROI": ["알오아이", "알 오 아이"],
        "E2E": ["이투이", "이 투 이", "엔드투엔드"],
        "End-to-End": ["엔드 투 엔드", "엔드투엔드"],
        "Full-Stack": ["풀스택", "풀 스택"],
        "AI-Native": ["에이아이 네이티브", "에이아이네이티브"],

        # AI/ML terms
        "AI": ["에이아이", "에이 아이"],
        "LLM": ["엘엘엠", "엘 엘 엠"],
        "RAG": ["래그", "랙"],
        "GPT": ["지피티", "지 피 티"],
        "Agent": ["에이전트", "에이 전트"],
        "Workflow": ["워크플로우", "워크 플로우", "워크플로"],
        "Prompt": ["프롬프트", "프롬프"],
        "MNIST": ["엠니스트", "엠 니스트"],
        "ML/DL": ["엠엘디엘", "머신러닝딥러닝"],

        # Business terms
        "Profit & Loss": ["프로핏앤로스", "프로핏 앤 로스"],
        "Product Owner": ["프로덕트 오너", "프로덕트오너"],
        "PO": ["피오", "피 오"],
        "Consultant": ["컨설턴트", "컨설 턴트"],
        "Startup": ["스타트업", "스타트 업"],
        "Playbook": ["플레이북", "플레이 북"],

        # Tools and platforms
        "CODEX": ["코덱스", "코 덱스"],
        "FastForward": ["패스트포워드", "패스트 포워드"],
        "n8n": ["엔에잇엔", "엔8엔"],
        "NotebookLM": ["노트북엘엠", "노트북 엘엠"],

        # Common tech terms
        "API": ["에이피아이", "에피아이"],
        "SaaS": ["사스", "싸스"],
        "SDK": ["에스디케이", "에스디 케이"],
        "GTM": ["지티엠", "지 티 엠"],
        "UX": ["유엑스", "유 엑스"],
        "MECE": ["미시", "미씨", "엠이씨이"],
        "HITP": ["에이치아이티피", "에이치 아이 티 피"],

        # People/Companies
        "a16z": ["에이식스틴지", "에이16지"],
        "벤 호로위츠": ["벤호로위츠"],
        "일론 머스크": ["일론머스크"],
    }

    # Common AI/tech terms
    general_tech_terms = {
        "Claude": ["클로드", "클로우드"],
        "OpenAI": ["오픈에이아이", "오픈 에이아이"],
        "Anthropic": ["앤트로픽", "안트로픽"],
        "Python": ["파이썬", "파이선"],
        "Embedding": ["임베딩", "엠베딩"],
        "Fine-tuning": ["파인튜닝", "파인 튜닝"],
        "Token": ["토큰"],
        "Transformer": ["트랜스포머", "트랜스 포머"],
        "Vector DB": ["벡터디비", "벡터 디비"],
    }

    # Merge all terms
    all_terms = {**presentation_specific_terms, **general_tech_terms}

    if pdf_path and os.path.exists(pdf_path):
        print(f"Reference PDF found: {os.path.basename(pdf_path)}")
        print(f"Using {len(all_terms)} terminology corrections from 건호님's presentation")
    else:
        print(f"Warning: PDF not found at {pdf_path}")
        print(f"Using {len(all_terms)} common B2B/AX/AI terminology corrections")

    return all_terms

def correct_terminology(segments, corrections):
    """Apply terminology corrections to segments"""
    corrected_segments = []
    correction_count = 0
    duplicate_count = 0
    prev_text = ""

    for seg in segments:
        text = seg['text']
        original_text = text

        # Apply each correction
        for correct_term, variations in corrections.items():
            for variation in variations:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(variation), re.IGNORECASE)
                text = pattern.sub(correct_term, text)

        if text != original_text:
            correction_count += 1

        # 유니코드 정규화 후 연속 중복 체크
        normalized_text = unicodedata.normalize('NFC', text.strip())
        normalized_prev = unicodedata.normalize('NFC', prev_text.strip())

        if normalized_text == normalized_prev:
            duplicate_count += 1
            continue  # 연속 중복 스킵

        corrected_segments.append({
            'index': seg['index'],
            'timestamp': seg['timestamp'],
            'text': text
        })
        prev_text = text

    return corrected_segments, correction_count, duplicate_count

def write_srt(segments, output_path):
    """Write segments to SRT file"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{seg['timestamp']}\n")
            f.write(f"{seg['text']}\n\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python subtitle_corrector.py <srt_file> [pdf_reference] [output_file]")
        print()
        print("Example:")
        print("  python subtitle_corrector.py meetup_02_건호님.srt slides/4-신건호-*.pdf")
        sys.exit(1)

    srt_path = sys.argv[1]
    pdf_path = sys.argv[2] if len(sys.argv) >= 3 else None
    output_path = sys.argv[3] if len(sys.argv) >= 4 else srt_path

    if not os.path.exists(srt_path):
        print(f"Error: SRT file not found: {srt_path}")
        sys.exit(1)

    print("=" * 70)
    print("STEP 3: Terminology Correction (건호님's AX Presentation)")
    print("=" * 70)
    print(f"SRT file: {srt_path}")
    if pdf_path:
        print(f"Reference PDF: {pdf_path}")
    print(f"Output: {output_path}")
    print()

    # Read SRT
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    segments = parse_srt(content)
    print(f"Loaded {len(segments)} segments")

    # Extract terms from PDF
    corrections = extract_keywords_from_pdf(pdf_path) if pdf_path else {}

    # Apply corrections
    corrected_segments, correction_count, duplicate_count = correct_terminology(segments, corrections)

    # Write corrected SRT
    write_srt(corrected_segments, output_path)

    print()
    print(f"Corrections applied: {correction_count} segments modified")
    if duplicate_count > 0:
        print(f"Duplicates removed: {duplicate_count} consecutive duplicate segments")
    print(f"Output written to: {output_path}")
    print()
    print("=" * 70)
    print("SUBTITLE GENERATION PIPELINE COMPLETE")
    print("=" * 70)
    print()
    print("Please review the final SRT file and make manual corrections as needed.")

if __name__ == "__main__":
    main()
