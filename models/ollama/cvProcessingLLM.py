import pymupdf  # PyMuPDF
import docx
from docx import Document
import easyocr
import json
import os
from pathlib import Path
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
import time

try:
    from ..prompts import cvscoringPrompt as prompt
except:
    from prompts import cvscoringPrompt as prompt

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    print(text)
    return text


def extract_text_from_docx(docx_path):
    """Extract text from DOCX file"""
    doc = Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    print(text)
    return text


def extract_text_from_doc(doc_path):
    """Extract text from DOC file (older format)"""
    try:
        return extract_text_from_docx(doc_path)
    except Exception as e:
        print(f"Warning: Could not extract from .doc file: {e}")
        print("For .doc files, please convert to .docx or PDF format")
        return ""


def extract_text_from_image(image_path):
    """Extract text from image using EasyOCR"""
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    text = " ".join([detection[1] for detection in result])
    return text


def extract_resume_text(resume_path):
    """Extract text from resume based on file type"""
    file_ext = Path(resume_path).suffix.lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(resume_path)
    elif file_ext == '.docx':
        return extract_text_from_docx(resume_path)
    elif file_ext == '.doc':
        return extract_text_from_doc(resume_path)
    elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
        return extract_text_from_image(resume_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def read_job_description(txt_path):
    """Read job description from text file"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()


def evaluate_resume(resume_path, job_description_path, model_name="llama3.1"):
    """
    Evaluate resume using locally installed Ollama model
    
    Args:
        resume_path: Path to resume file (PDF, DOCX, DOC, or image)
        job_description_path: Path to job description text file
        model_name: Ollama model name (default: "llama3.1")
                   Options: "llama3.1", "llama2", "gemma2", "gemma:7b", etc.
    
    Returns:
        JSON object with evaluation results
    """
    
    # Extract text from resume
    print("Extracting text from resume...")
    resume_text = extract_resume_text(resume_path)
    
    # Read job description
    print("Reading job description...")
    job_description = read_job_description(job_description_path)
    
    # Initialize Ollama LLM
    print(f"Initializing Ollama model: {model_name}...")
    llm = Ollama(model=model_name, request_timeout=3000.0, temperature=0.3)
    
    # Set global settings
    Settings.llm = llm
    
    # Prepare the prompt
    system_prompt = ast()
    user_prompt = f"""RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Evaluate this resume against the job description and return ONLY the JSON output as specified. No additional text."""
    
    # Create chat messages
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_prompt)
    ]
    
    # Generate response
    print("Generating evaluation...")
    response = llm.chat(messages)
    
    # Extract JSON from response
    try:
        response_text = response.message.content
        
        # Try to find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            return result
        else:
            print("Raw response:", response_text)
            return {"error": "Could not find valid JSON in response"}
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print("Raw response:", response_text)
        return {"error": "Invalid JSON in response", "raw_response": response_text}
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}


def main():
    """Main function to run the resume evaluator"""
    
    # Example usage
    resume_path = "cvs/resume_1.pdf"
    job_description_path = "jds/jd_1.txt"
    
    # Available models (must be installed via Ollama first):
    # "llama3.1" or "llama3.1:8b" - LLaMA 3.1 8B
    # "llama2" or "llama2:7b" - LLaMA 2 7B
    # "gemma2" or "gemma2:9b" - Gemma 2 9B
    # "gemma:7b" - Gemma 7B
    
    model_name = "gemma3:4b"
    start_time = time.time()
    result = evaluate_resume(resume_path, job_description_path, model_name)
    print(f"time taken is  : {time.time() - start_time}")
    
    # Print formatted JSON
    print("\n" + "="*50)
    print("EVALUATION RESULT:")
    print("="*50)
    print(json.dumps(result, indent=2))
    
    # Optionally save to file
    with open('evaluation_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nResult saved to evaluation_result.json")


if __name__ == "__main__":
    main()