from typing import Optional, List
from dataclasses import dataclass
from preprocessing import RichTextBlock
from rules import calculate_heading_score
from transformers import AutoTokenizer, AutoModel
import torch
import uuid

# Load BERT model and tokenizer
TOKENIZER = AutoTokenizer.from_pretrained('./pretrained_models_bert_tiny')
BERT_MODEL = AutoModel.from_pretrained('./pretrained_models_bert_tiny')
BERT_MODEL.eval()

# Rule-based thresholds
H1_THRESHOLD = 10
H2_THRESHOLD = 7
H3_THRESHOLD = 4

@dataclass
class ClassifiedHeading:
    """A data structure to hold a block classified as a heading, matching original output format."""
    id: int
    label: str
    parent_id: int
    order: int
    confidence: float
    text: str
    gt_text: str
    box: List[float]
    page: int
    heading_level: str

class CompactDocumentModel:
    """Mock CompactDocumentModel for BERT-based classification."""
    def predict(self, inputs):
        # Mock prediction: Replace with actual model inference
        with torch.no_grad():
            outputs = BERT_MODEL(**inputs)
        logits = outputs.last_hidden_state.mean(dim=1)
        labels = torch.argmax(logits[:, :3], dim=1)  # 0=title, 1=section-title, 2=other
        orders = torch.argmax(logits[:, 3:10], dim=1)  # Order 0-6
        confidences = torch.softmax(logits[:, :3], dim=1).max(dim=1).values
        predictions = []
        for i, (label, order, conf) in enumerate(zip(labels, orders, confidences)):
            label_str = ["title", "section-title", "other"][label.item()]
            order_val = order.item()
            heading_level = "other"
            if label_str in ["title", "section-title"]:
                if order_val <= 1:
                    heading_level = "h1"
                elif order_val <= 3:
                    heading_level = "h2"
                else:
                    heading_level = "h3"
            predictions.append({
                "id": i + 1,
                "label": label_str,
                "parent_id": 0,  # Simplified: Update with actual parent_id logic
                "order": order_val,
                "confidence": conf.item(),
                "heading_level": heading_level
            })
        return predictions

def get_heading_level_rule_based(block: RichTextBlock, body_font_size: float) -> Optional[int]:
    """
    Classifies a text block as H1, H2, H3, or None using the rule-based scoring engine.
    """
    score = calculate_heading_score(block, body_font_size)
    if score >= H1_THRESHOLD:
        return 1
    elif score >= H2_THRESHOLD:
        return 2
    elif score >= H3_THRESHOLD:
        return 3
    return None

def get_heading_level_bert(blocks: List[RichTextBlock]) -> List[ClassifiedHeading]:
    """
    Classifies blocks using BERT-based CompactDocumentModel.
    Returns detailed ClassifiedHeading objects.
    """
    texts = [block.text for block in blocks]
    inputs = TOKENIZER(texts, padding=True, truncation=True, return_tensors="pt", max_length=512)
    model = CompactDocumentModel()  # Replace with actual model
    predictions = model.predict(inputs)
    
    headings = []
    for block, pred in zip(blocks, predictions):
        if pred["label"] in ["title", "section-title"]:
            headings.append(ClassifiedHeading(
                id=pred["id"],
                label=pred["label"],
                parent_id=pred["parent_id"],
                order=pred["order"],
                confidence=pred["confidence"],
                text=block.text,
                gt_text="",  # Placeholder: Update with ground truth if available
                box=block.bbox,
                page=block.page_num,
                heading_level=pred["heading_level"]
            ))
    return headings

def classify_blocks(blocks: List[RichTextBlock], body_font_size: float, use_bert: bool = False) -> List[ClassifiedHeading]:
    """
    Filters and classifies a list of RichTextBlocks into a list of headings.
    Tries rule-based classification first; uses BERT if specified.
    """
    classified_headings: List[ClassifiedHeading] = []
    
    if not use_bert:
        # Rule-based classification
        for i, block in enumerate(blocks):
            if block.bbox[2] < 50 or block.bbox[3] > 742:  # Filter headers/footers
                continue
            level = get_heading_level_rule_based(block, body_font_size)
            if level is not None:
                heading_level = f"h{level}"
                classified_headings.append(ClassifiedHeading(
                    id=i + 1,
                    label="section-title" if level > 1 else "title",
                    parent_id=0,  # Simplified: Update with linker logic
                    order=level - 1,
                    confidence=0.9,  # Placeholder: Rule-based confidence
                    text=block.text,
                    gt_text="",  # Placeholder: Update with ground truth
                    box=block.bbox,
                    page=block.page_num,
                    heading_level=heading_level
                ))
    else:
        # BERT-based classification
        headings = get_heading_level_bert(blocks)
        for heading in headings:
            if heading.box[2] < 50 or heading.box[3] > 742:  # Filter headers/footers
                continue
            classified_headings.append(heading)
    
    return classified_headings