from typing import List, Dict, Any
from model import ClassifiedHeading

def build_hierarchy(document_title: str, classified_headings: List[ClassifiedHeading]) -> Dict[str, Any]:
    """
    Builds a nested hierarchical dictionary from a flat list of classified headings.
    Uses a stack-based approach and includes a de-duplication check.
    Maps heading_level ('h1', 'h2', 'h3') to integer levels for hierarchy construction.
    """
    root = {"title": document_title, "outline": []}
    stack: List[Dict] = [root]
    last_heading_text = None  # Keep track of the last added heading

    # Map heading_level to integer for hierarchy
    level_map = {"h1": 1, "h2": 2, "h3": 3, "other": 4}

    for heading in classified_headings:
        # DE-DUPLICATION LOGIC: Skip if current heading text is the same as the last one
        if heading.text == last_heading_text:
            continue

        # Get integer level from heading_level
        current_level = level_map.get(heading.heading_level, 4)
        parent_level = stack[-1].get("level_val", 0)

        # Pop stack until we find the correct parent level
        while stack and parent_level >= current_level:
            stack.pop()
            parent_level = stack[-1].get("level_val", 0)

        correct_parent_node = stack[-1]
        
        new_heading_node = {
            "level": f"H{current_level}",
            "text": heading.text,
            "page": heading.page,
            "outline": [],
            "level_val": current_level,
        }
        
        correct_parent_node["outline"].append(new_heading_node)
        stack.append(new_heading_node)
        
        # Update the last seen heading text
        last_heading_text = heading.text

    def cleanup_keys(node: Dict):
        if "level_val" in node:
            del node["level_val"]
        for child in node.get("outline", []):
            cleanup_keys(child)
    
    cleanup_keys(root)
    return root