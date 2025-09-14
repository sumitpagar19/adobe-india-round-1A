
# PDF Outline Extractor: Your Smart PDF Navigator

## Overview

Do you ever find yourself lost in a long PDF, desperately trying to find a specific section, or wishing you could quickly grasp its main points without endless scrolling? We've all been there! That's why we built the PDF Outline Extractor.

Imagine being able to instantly jump to any chapter, subheading, or section in *any* PDF, no matter how complex or even if it's a scanned document. Our system does just that: it takes any PDF and creates a super-helpful, structured outline (like a Table of Contents on steroids!) in a clean, easy-to-use JSON format.

What makes our system special? It's designed to truly *understand* how different parts of a document relate to each other, like a human reader would. Plus, it works completely **offline**, processes a 50-page document in **under 10 seconds**, and uses a tiny model (less than 20MB!). The best part? It's built to handle **any language** thanks to its clever visual approach, with extra support for English and Chinese documents.

* **Want to see it in action?** [Click here for a quick demo video!](https://youtu.be/Nktx6GHzZT4)
* **A Detailed Documentation of our solution:** [Click here](documentation%20and%20demo/APIcalypse%20Documentation_Adobe%20Round%201a.pdf)

---

## Our Approach & How It Works

Our journey started with some advanced AI models, but we quickly realized that just relying on AI wasn't enough to perfectly understand the hierarchy of a document.

So, we changed our strategy! We created a clever "hybrid" system that "thinks like a human reader". It first looks at the visual clues in a document, just like you would. Then, if needed, a small but mighty AI model (called BERT-tiny, about 17-18 MB) steps in as a smart assistant, making sure we get the best possible outline.

### 1. The Core Engine: Combining Text and Layout

At the core of our system is a super-fast, smart engine that literally *sees* your document. Instead of just reading words, it analyzes how text *looks* on the page. For every line, it checks things like:

* **Font Size:** Is it bigger than the regular text? That's a strong hint it's a heading!
* **Boldness:** Is the text bold? Another big clue for headings.
* **Positioning:** Where is the text on the page? Is it indented? Does it have extra space around it? These details tell us about its importance.
* **Text Patterns:** Does it look like a typical heading, like "1. Introduction" or "CHAPTER 3"?

This "visual-first" approach is incredibly powerful because it works with **any language**. The way headings are designed visually (bigger, bolder, indented) is pretty universal, no matter if it's English, Chinese, or anything else!

### 2. The Full Processing Pipeline

![Pipeline](documentation%20and%20demo/Round%201a%20Pipeline.png)

Our system takes your PDF through a robust process to ensure you get a super accurate outline:

1.  **Smart Text Extraction:** For most digital PDFs, we use a tool called **PyMuPDF**. But if a page looks like it has very little text (maybe it's a scanned image!), our system smartly switches to **Tesseract OCR** to "read" the image and extract the text. Then, we clean everything up.
2.  **First Pass - Visual Classification:** Our clever visual engine performs the initial classification of text lines into Title, H1, H2, or H3. This is where our rules really shine!
3.  **Building the Hierarchy:** This is a crucial step! A deterministic, **stack-based algorithm** processes classified headings to flawlessly reconstruct parent-child relationships and build a perfect nested hierarchy.
4.  **ML as a Backup (Just in Case!):** Our small but powerful **BERT-tiny ML model** is triggered **only if the rule-based engine yields insufficient headings** (e.g., unusually sparse outline, or a short PDF with too few headings). This makes sure our system is super reliable and always finds an outline if one exists.

### 3. BERT-tiny: Our Intelligent "Expert Consultant"

Think of our **BERT-tiny model** (only 17-18MB!) as an expert consultant that we call in only when needed. This strategic placement leverages the contextual power of machine learning precisely when needed.

It's activated when the rule-based classification yields too few headings for a given PDF (e.g., less than `max(3, page_count)` headings).

**When BERT-tiny steps in, here's what it does:**
* **Understands Text Context:** Converts text into numerical embeddings.
* **Combines Clues:** Combines box coordinates (intrinsic properties like X and Y coordinates), text embeddings, and spatial information.
* **Smart Classification:** Classifies elements as titles or headings.
* **Connects the Dots:** Predicts linking, aiding in hierarchical understanding and preventing self-linking.
* **Custom Training:** Utilizes a custom loss function prioritizing linking/hierarchy losses and mismatch in order. An attention mask is also applied.

**Good to know:** While our main **rule-based system** works for **all languages**, the **BERT-tiny fallback model** can classify documents in various languages, but it's **specially optimized for English and Chinese** as it was trained on the **DocHieNet dataset**.

---

## Performance & Training

Our system isn't just good; it's really fast and efficient, especially for typical documents!

| What We Measure | Our Results |
| :------------------- | :------------------------------------------ |
| **Speed** | **Super Fast:** < 10 seconds for PDFs under 50 pages! |
| **Size** | Approximately **18MB** (BERT-tiny, used as fallback) |
| **Internet Needed?** | **None!** (completely offline) |
| **Compatibility** | `linux/amd64` (Docker compatible) |
| **Languages** | Fully multilingual (rule engine); ML fallback supports English + Chinese |

---

## Setup & Running the Extractor

We use Docker to make setting up and running our extractor super simple and portable.

### Build the Docker Image

Just run this command in your **powershell** terminal:

```bash
docker build --platform linux/amd64 -t apicalypse-extractor:latest .
```

### Run the Docker Container

1.  Place your PDFs in the `input/` folder.
2.  Then, run this command on **powershell**:

    ```bash
    docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none apicalypse-extractor:latest
    ```

Your extracted JSON outlines will magically appear in the `output/` folder.

-----

## Folder Structure

Here's a quick look at how our project is organized:

```
APIcaypse-Round-1a
├── documentation and demo/        # You will find the documentation, demo video and pipeline of our solution here
├── input/                         # Drop your PDFs here
├── output/                        # Your JSON outlines will appear here.
├── performance/                   # Contains pre-generated outputs from Rule-Based and ML models in different test cases
├── src/                           # All the brains of the operation live here!
|   ├── pretrained_models_bert_tiny/
│   ├── linker.py
│   ├── model.py
│   ├── preprocessing.py
│   ├── rules.py
│   └── run.py
├── Dockerfile                     # Docker instructions.
├── requirements.txt               # List of what our project needs to run.
└── README.md                      # (This file you're reading!)
```
-----

### What is in the `performance/` folder:
The `performance/` folder contains reference outputs from selected test PDFs and is **not generated during normal Docker execution**.

Each subfolder corresponds to a sample PDF and includes:
- `file_hierarchical_output.json`:  
  The final nested outline (Title, H1, H2, H3) produced by our system.

- `file_model_output.json` *(if present)*:  
  Indicates that the BERT fallback was activated. This file shows the raw output from the ML model before post-processing.

These examples illustrate how our pipeline handles a wide range of documents — from clean layouts to complex or noisy PDFs — and when the ML fallback contributes to the final result.


## Output JSON Format

Here's an example of the structured outline you'll get:

```json
{
  "title": "Sample PDF Title",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "Deep Learning", "page": 2 },
    { "level": "H3", "text": "Transformer Networks", "page": 3 }
  ]
}
```

You can see the main title, and then a clear list of headings, their levels (H1, H2, H3), what they say, and which page they're on. Super handy!

-----

## Technology & Datasets

Our solution is built with a solid foundation of modern technologies, and we trained our AI models using the **DocHieNet dataset**. We carefully split this data (70% for training, 10% for validating, and 20% for testing) to make sure our system is smart and reliable.

| What it Does | How We Do It |
| :------------------ | :------------------------------------ |
| **Primary Extractor** | PyMuPDF (Fitz) |
| **OCR Fallback** | Tesseract, pdfplumber, pdf2image |
| **Core Logic** | Custom Visual Rule Engine & Stateful Linker |
| **ML Fallback Model** | BERT-tiny |
| **Model Training** | Custom Loss Function, Attention Mask |
| **Frameworks** | PyTorch, Transformers |

-----

## What Kind of PDFs Can It Handle?

Our solution is exceptionally robust and delivers outstanding results across a wide variety of document types and structures, making it broadly applicable across diverse domains like healthcare, business, and academia:

  * Academic and research papers (IEEE, ACM formats)
  * Business and annual reports
  * Scanned documents and image-based PDFs
  * Textbooks with complex, multi-column layouts
  * Pages with low text content or unusual formatting
  * PowerPoint presentations converted to PDF format.
  * Complex PDFs not adhering to a simple rule-based structure.
  * Multilingual documents.

-----

## Team APIcalypse

  * [Nandini Nema](https://www.linkedin.com/in/nandininema/)
  * [Soham Chandane](https://www.linkedin.com/in/sohamchandane/)
  * [Parv Siria](https://www.linkedin.com/in/parv-siria/)

-----

## Conclusion

This project, the **PDF Outline Extractor**, offers a high-accuracy solution for unlocking structured intelligence from any PDF. We built it to be fast, dependable, and universally useful, directly solving the tough problem of hierarchical linking. Our unique approach, combining a robust, language-agnostic rule-based engine with an intelligent, compact ML fallback, provides a powerful foundation. This "plug-and-play" module is poised to revolutionize advanced applications like semantic search, automated summarization, and intelligent document interlinking for future stages and beyond.
