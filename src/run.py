import os
import json
import time
from pathlib import Path
from preprocessing import extract_rich_text_blocks, get_document_baseline_font_size
from model import classify_blocks, ClassifiedHeading
from linker import build_hierarchy
from typing import List, Dict, Any

# For local development, use relative paths
INPUT_DIR = "../input"
OUTPUT_DIR = "../output"
MODEL_PERF_DIR = "../performance"

def find_document_title(blocks: List, headings: List[ClassifiedHeading]) -> str:
    """
    Selects the title as the H1 heading with the largest font size from page 0.
    Falls back to the first non-empty block if no H1 is found.
    """
    if not blocks:
        return "Untitled Document"
    
    # Prefer H1 from page 0 with largest font size
    page_zero_h1 = [h for h in headings if h.heading_level == "h1" and h.page == 0]
    if page_zero_h1:
        block_map = {b.text: b for b in blocks}
        valid_h1 = [h for h in page_zero_h1 if h.text in block_map]
        if valid_h1:
            return max(valid_h1, key=lambda h: block_map[h.text].font_size).text
    
    # Fallback: First non-empty block from page 0
    first_page_blocks = [b for b in blocks if b.page_num == 0][:10]
    if first_page_blocks:
        title_block = max(first_page_blocks, key=lambda b: b.font_size)
        if title_block.text.strip() and title_block.text != "[EMPTY]":
            return title_block.text
    
    # Final fallback: First non-empty block
    for block in blocks:
        if block.text.strip() and block.text != "[EMPTY]":
            return block.text
    
    return "Untitled Document"

def save_flat_output(headings: List[ClassifiedHeading], title: str, output_path: str):
    """
    Saves headings in the flat JSON format with level as H1/H2/H3 and 0-based page numbers.
    """
    output = {
        "title": title,
        "outline": [
            {
                "level": heading.heading_level.upper(),
                "text": heading.text,
                "page": heading.page
            }
            for heading in headings
        ]
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

def save_hierarchical_output(headings: List[ClassifiedHeading], title: str, output_path: str):
    """
    Saves the hierarchical output using linker.py's build_hierarchy.
    Uses the 'outline' field to avoid redundant title wrapper and filters title repetition.
    """
    hierarchical_root = build_hierarchy(title, headings)
    hierarchical_outline = hierarchical_root.get("outline", [])
    output = {
        "title": title,
        "outline": [
            {
                "level": h["level"],
                "text": h["text"],
                "page": h["page"],
                "outline": h["outline"]
            }
            for h in hierarchical_outline
            if h["text"].strip() and h["text"] != title
        ]
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

def save_model_output(headings: List[ClassifiedHeading], output_path: str):
    """
    Saves detailed BERT model output in the original format to MODEL_PERF_DIR.
    """
    output = [
        {
            "id": heading.id,
            "label": heading.label,
            "parent_id": heading.parent_id,
            "order": heading.order,
            "confidence": heading.confidence,
            "text": heading.text,
            "gt_text": heading.gt_text,
            "box": heading.box,
            "page": heading.page,
            "heading_level": heading.heading_level
        }
        for heading in headings
    ]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

def process_single_pdf(file_path: str):
    """
    Runs the full extraction and hierarchy construction pipeline for one PDF.
    Tries rule-based classification; falls back to BERT if insufficient headings.
    Saves detailed BERT output in MODEL_PERF_DIR.
    """
    start_time = time.time()
    filename = os.path.basename(file_path)
    print(f"Processing {filename}...")

    try:
        # Preprocessing: Extract rich text blocks with visual features
        processing_path = file_path
        preprocess_start = time.time()
        rich_text_blocks = extract_rich_text_blocks(processing_path)
        preprocess_time = time.time() - preprocess_start
        print(f"Preprocessing {filename} took {preprocess_time:.2f} seconds")
        
        if not rich_text_blocks:
            print(f"Could not extract any text blocks from {filename}. Skipping.")
            return

        # Analysis: Determine baseline font
        baseline_font_size = get_document_baseline_font_size(rich_text_blocks)
        
        # Classification: Try rule-based first
        rule_based_headings = classify_blocks(rich_text_blocks, baseline_font_size, use_bert=False)
        
        # Fallback to BERT if rule-based yields insufficient headings
        page_count = max(b.page_num for b in rich_text_blocks) + 1
        min_headings = max(3, page_count)  # Expect at least 3 or 1 per page
        final_headings = rule_based_headings
        bert_headings = None
        if len(rule_based_headings) < min_headings:
            print(f"Rule-based classification yielded {len(rule_based_headings)} headings for {filename}. Falling back to BERT...")
            bert_headings = classify_blocks(rich_text_blocks, baseline_font_size, use_bert=True)
            final_headings = bert_headings
        
        # Find document title
        doc_title = find_document_title(rich_text_blocks, final_headings)
        
        # Define output paths
        output_filename = Path(file_path).stem + ".json"
        hierarchical_output_filename = Path(file_path).stem + "_hierarchical_output.json"
        model_output_filename = Path(file_path).stem + "_model_output.json"
        flat_output_path = os.path.join(OUTPUT_DIR, output_filename)
        hierarchical_output_path = os.path.join(MODEL_PERF_DIR, hierarchical_output_filename)
        model_output_path = os.path.join(MODEL_PERF_DIR, model_output_filename)

        # Ensure output directories exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(MODEL_PERF_DIR, exist_ok=True)
        
        # Save flat output (rule-based or BERT)
        save_flat_output(final_headings, doc_title, flat_output_path)
        print(f"Saved flat output to {flat_output_path}")
        
        # Save hierarchical output (rule-based or BERT)
        save_hierarchical_output(final_headings, doc_title, hierarchical_output_path)
        print(f"Saved hierarchical output to {hierarchical_output_path}")
        
        # Save detailed BERT model output
        if bert_headings is not None:
            save_model_output(bert_headings, model_output_path)
            print(f"Saved BERT model output to {model_output_path}")
        
        end_time = time.time()
        print(f"Finished {filename} in {end_time - start_time:.2f} seconds")
    
    except Exception as e:
        print(f"An error occurred while processing {filename}: {e}")

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(MODEL_PERF_DIR):
        os.makedirs(MODEL_PERF_DIR)

    # Process all PDFs in the input directory
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {INPUT_DIR}.")
    else:
        for filename in pdf_files:
            full_path = os.path.join(INPUT_DIR, filename)
            process_single_pdf(full_path)