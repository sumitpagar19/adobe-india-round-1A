import pdfplumber
import pytesseract
from dataclasses import dataclass
from typing import List, Tuple
from collections import Counter, defaultdict
from PIL import Image
import platform
import time
import re

# Set the Tesseract executable path for Windows
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def clean_text(text):
    """
    Clean text by collapsing repeated characters, normalizing whitespace, and stripping.
    Args:
        text (str): Input text.
    Returns:
        Cleaned text string.
    """
    text = re.sub(r'(.)\1{2,}', r'\1', text)  # Collapse 3+ repeated chars
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

@dataclass
class RichTextBlock:
    """A structured representation of a text block with its visual and positional attributes."""
    text: str
    bbox: Tuple[float, float, float, float]
    font_size: float
    font_name: str
    is_bold: bool
    is_italic: bool
    page_num: int
    block_id: int

def post_process_blocks(blocks: List[RichTextBlock]) -> List[RichTextBlock]:
    """
    Merges fragmented text blocks on the same line and removes duplicates/substrings.
    Optimized for speed by minimizing iterations.
    """
    if not blocks:
        return []

    # Group blocks by page and approximate vertical line
    line_groups = defaultdict(list)
    y_tolerance = 5

    for block in blocks:
        if not isinstance(block, RichTextBlock) or not block.text.strip() or block.text == "[EMPTY]":
            continue
        line_key = (block.page_num, round(block.bbox[1] / y_tolerance))
        line_groups[line_key].append(block)

    # Merge fragments within each line group
    merged_blocks: List[RichTextBlock] = []
    for key, group in line_groups.items():
        if not group:
            continue
        
        group.sort(key=lambda b: b.bbox[0])
        full_text = " ".join(b.text for b in group if b.text.strip())
        
        if not full_text.strip():
            continue
            
        x0 = min(b.bbox[0] for b in group)
        y0 = min(b.bbox[1] for b in group)
        x1 = max(b.bbox[2] for b in group)
        y1 = max(b.bbox[3] for b in group)
        
        dominant_block = max(group, key=lambda b: b.font_size)
        
        merged_blocks.append(RichTextBlock(
            text=full_text,
            bbox=(x0, y0, x1, y1),
            font_size=dominant_block.font_size,
            font_name=dominant_block.font_name,
            is_bold=dominant_block.is_bold,
            is_italic=dominant_block.is_italic,
            page_num=dominant_block.page_num,
            block_id=dominant_block.block_id
        ))

    # De-duplicate by removing substrings
    sorted_for_dedup = sorted(merged_blocks, key=lambda b: (b.page_num, -len(b.text)))
    final_blocks: List[RichTextBlock] = []
    seen_on_page = defaultdict(list)

    for block in sorted_for_dedup:
        page_seen_texts = seen_on_page[block.page_num]
        if any(block.text in seen_text for seen_text in page_seen_texts):
            continue
        final_blocks.append(block)
        page_seen_texts.append(block.text)
            
    return sorted(final_blocks, key=lambda b: (b.page_num, b.bbox[1], b.bbox[0]))

def extract_rich_text_blocks(pdf_path: str) -> List[RichTextBlock]:
    """
    Extracts text using pdfplumber for digital text, with OCR fallback when fewer than 5 lines are extracted.
    Cleans text with clean_text function to remove repeated characters and normalize whitespace.
    Uses 0-based page numbering for page_num.
    Outputs RichTextBlock objects for compatibility with rule-based classification.
    """
    start_time = time.time()
    initial_blocks: List[RichTextBlock] = []
    current_block_id = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                # Try pdfplumber text extraction
                lines = list(page.extract_text_lines())
                if lines and any(line.get("text", "").strip() for line in lines) and len(lines) >= 5:
                    # Process digital text lines
                    for line in lines:
                        text = line.get("text", "").strip()
                        if not text:
                            continue
                        text = clean_text(text)  # Clean extracted text
                        if not text:
                            continue
                        box = [line["x0"], line["top"], line["x1"], line["bottom"]]
                        if any(coord < 0 or coord > max(page.width, page.height) for coord in box):
                            continue
                        char = line.get("chars", [{}])[0]
                        font_size = char.get("size", 12.0)
                        font_name = char.get("fontname", "Unknown").lower()
                        is_bold = "bold" in font_name or char.get("fontweight", 400) >= 700
                        is_italic = "italic" in font_name
                        rich_block = RichTextBlock(
                            text=text,
                            bbox=tuple(box),
                            font_size=round(font_size, 2),
                            font_name=font_name,
                            is_bold=is_bold,
                            is_italic=is_italic,
                            page_num=page_idx,  # 0-based page numbering
                            block_id=current_block_id
                        )
                        initial_blocks.append(rich_block)
                        current_block_id += 1
                else:
                    # Fallback to OCR
                    print(f"Page {page_idx} has fewer than 5 lines or no text. Attempting OCR...")
                    try:
                        pil_img = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(
                            pil_img, lang='eng', config='--psm 6 -c tessedit_do_invert=0', timeout=2
                        )
                        if ocr_text.strip():
                            for line in ocr_text.split('\n'):
                                line = line.strip()
                                if not line:
                                    continue
                                line = clean_text(line)  # Clean OCR text
                                if not line:
                                    continue
                                rich_block = RichTextBlock(
                                    text=line,
                                    bbox=(0, 0, page.width, page.height),
                                    font_size=12.0,
                                    font_name="OCR",
                                    is_bold=False,
                                    is_italic=False,
                                    page_num=page_idx,  # 0-based page numbering
                                    block_id=current_block_id
                                )
                                initial_blocks.append(rich_block)
                                current_block_id += 1
                        else:
                            rich_block = RichTextBlock(
                                text="[EMPTY]",
                                bbox=(0, 0, page.width, page.height),
                                font_size=12.0,
                                font_name="OCR",
                                is_bold=False,
                                is_italic=False,
                                page_num=page_idx,  # 0-based page numbering
                                block_id=current_block_id
                            )
                            initial_blocks.append(rich_block)
                            current_block_id += 1
                    except Exception as ocr_error:
                        print(f"OCR fallback failed for page {page_idx}: {ocr_error}")
                        rich_block = RichTextBlock(
                            text="[EMPTY]",
                            bbox=(0, 0, page.width, page.height),
                            font_size=12.0,
                            font_name="OCR",
                            is_bold=False,
                            is_italic=False,
                            page_num=page_idx,  # 0-based page numbering
                            block_id=current_block_id
                        )
                        initial_blocks.append(rich_block)
                        current_block_id += 1
    except Exception as e:
        print(f"Error opening {pdf_path} with pdfplumber: {e}")
        return []

    # Apply post-processing to clean up all extracted blocks
    final_blocks = post_process_blocks(initial_blocks)
    print(f"Preprocessing {pdf_path} took {time.time() - start_time:.2f} seconds")
    return final_blocks

def get_document_baseline_font_size(blocks: List[RichTextBlock]) -> float:
    """Calculates the most common font size to establish a baseline for body text."""
    if not blocks:
        return 12.0
    
    font_sizes = [b.font_size for b in blocks if not b.is_bold and len(b.text.split()) < 50]
    
    if not font_sizes:
        font_sizes = [b.font_size for b in blocks]

    if not font_sizes:
        return 12.0
        
    most_common_list = Counter(font_sizes).most_common(1)
    
    if most_common_list:
        return most_common_list[0][0]
    else:
        return 12.0