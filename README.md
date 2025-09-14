PDF Outline Extractor: Your Smart PDF Navigator
Overview

Ever felt lost in a long PDF, endlessly scrolling to find a specific section?
That’s exactly why we built PDF Outline Extractor — a smart tool that automatically generates a structured outline (like a supercharged Table of Contents) for any PDF.

Key Highlights:

Works completely offline (no internet required).

Extracts outlines from any PDF — including scanned ones.

Processes 50-page documents in under 10 seconds.

Lightweight — only ~18 MB (BERT-tiny fallback model).

Language-agnostic visual approach (optimized for English & Chinese).

Watch Demo Video

Read Full Documentation

Our Approach

We designed a hybrid system that mimics how a human reads a document:

Rule-Based Visual Analysis

Detects font size, boldness, indentation, and spacing.

Identifies patterns like “1. Introduction” or “CHAPTER 3”.

Works across all languages.

Hierarchy Builder

A stack-based algorithm reconstructs parent-child heading relationships.

BERT-tiny Fallback (17–18MB)

Triggered only if too few headings are found.

Uses embeddings and layout information to classify headings.

Specially trained on the DocHieNet dataset (English + Chinese).

Performance
Metric	Result
Speed	< 10s for PDFs under 50 pages
Model Size	~18 MB
Internet	Not needed (fully offline)
Compatibility	linux/amd64 (Docker-ready)
Languages	All (rules) + English/Chinese (ML)
Setup & Usage
Build Docker Image
docker build --platform linux/amd64 -t pdf-extractor:latest .

Run Extractor

Place PDFs in the input/ folder.

Run:

docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none pdf-extractor:latest


Outlines will appear in the output/ folder.

Folder Structure
PDF-Outline-Extractor
├── documentation and demo/   # Documentation, demo video, pipeline
├── input/                    # Drop your PDFs here
├── output/                   # Extracted JSON outlines
├── performance/              # Sample outputs for testing
├── src/                      # Core source code
│   ├── pretrained_models_bert_tiny/
│   ├── linker.py
│   ├── model.py
│   ├── preprocessing.py
│   ├── rules.py
│   └── run.py
├── Dockerfile
├── requirements.txt
└── README.md

Output JSON Format

Example output:

{
  "title": "Sample PDF Title",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "Deep Learning", "page": 2 },
    { "level": "H3", "text": "Transformer Networks", "page": 3 }
  ]
}

Technology & Dataset
Component	Implementation
Primary Extractor	PyMuPDF (Fitz)
OCR Fallback	Tesseract, pdfplumber, pdf2image
Core Logic	Custom Visual Rule Engine & Stateful Linker
ML Fallback Model	BERT-tiny
Training Dataset	DocHieNet (70/10/20 split)
Frameworks	PyTorch, Transformers
Supported PDF Types

Academic and research papers (IEEE, ACM formats)

Business and annual reports

Scanned documents and image-based PDFs

Textbooks with multi-column layouts

Low-text or unusual formatting pages

Presentations converted to PDF

Complex, multilingual documents

Team

Sumit Pagar

Tushar Chtatrki

Rishikesh More
