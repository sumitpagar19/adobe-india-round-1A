from preprocessing import RichTextBlock
import re

def calculate_heading_score(block: RichTextBlock, body_font_size: float) -> int:
    """
    Calculates a score indicating the likelihood of a text block being a heading
    based on a set of weighted, relative visual heuristics.

    Args:
        block: The RichTextBlock to evaluate.
        body_font_size: The baseline body font size for the document.

    Returns:
        An integer score. Higher scores indicate a higher likelihood of being a major heading.
    """
    score = 0
    font_size = block.font_size

    # Rule 1: Relative Font Size (Primary Indicator) [9, 10]
    if font_size > 1.8 * body_font_size:
        score += 5
    elif 1.3 * body_font_size < font_size <= 1.8 * body_font_size:
        score += 3
    elif 1.1 * body_font_size < font_size <= 1.3 * body_font_size:
        score += 2
    
    # Rule 2: Font Weight (Bold is a strong signal) [11]
    if block.is_bold:
        score += 3

    # Rule 3: Text Case (All caps is a common heading style) [12]
    if block.text.isupper() and len(block.text.split()) > 1:
        score += 2

    # Rule 4: Content - Numbering (e.g., "1.", "2.1", "A.") [2]
    if re.match(r"^((\d+(\.\d+)*)|([A-Z]\.))\s", block.text):
        score += 5

    # Rule 5: Content - Brevity (Headings are typically short) [11]
    if len(block.text.split()) < 10:
        score += 1

    # Rule 6: Content - Syntax (Headings rarely end with a period) [13]
    if not block.text.endswith('.'):
        score += 1
        
    return score