import pymupdf  # PyMuPDF
import docx
from docx import Document
import easyocr
import json
import os
from pathlib import Path
from google import genai
import time
try:
    from prompts import cvscoringPrompt as prompt
    import models.gemini.creds as creds
except:
    from ..prompts import cvscoringPrompt as prompt
    from . import creds








def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    # print(text)
    return text


def extract_text_from_docx(docx_path):
    """Extract text from DOCX file"""
    doc = Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    # print(text)
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


def evaluate_resume(resume_path, job_description_path, model_name="gemini-2.5-flash"):
    """
    Evaluate resume using Google Gemini API
    
    Args:
        resume_path: Path to resume file (PDF, DOCX, DOC, or image)
        job_description_path: Path to job description text file
        model_name: Gemini model name (default: "gemini-2.0-flash-exp")
                   Options: "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash", etc.
        api_key: Google API key (optional, can also be set via environment variable)
    
    Returns:
        JSON object with evaluation results
    """
    
    # Extract text from resume
    api_key = creds.GOOGLE_API_KEY
    print("Extracting text from resume...")
    resume_text = extract_resume_text(resume_path)
    
    # Read job description
    print("Reading job description...")
    job_description = read_job_description(job_description_path)
    
    # Initialize Gemini client
    print(f"Initializing Gemini model: {model_name}...")
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        client = genai.Client()  # Uses GOOGLE_API_KEY environment variable
    
    # Prepare the prompt
    system_prompt = prompt.ast()
    user_prompt = f"""RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Evaluate this resume against the job description and return ONLY the JSON output as specified. No additional text."""
    
    # Combine system and user prompts
    full_prompt = f"""{system_prompt}

{user_prompt}"""
    
    # Generate response
    print("Generating evaluation...")
    response = client.models.generate_content(
        model=model_name,
        contents=full_prompt
    )
    
    # Extract JSON from response
    try:
        response_text = response.text
        
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
    
    # Available Gemini models:

    # "gemini-2.0-flash-exp" - Experimental flash model
    # "gemini-1.5-pro" - Pro model with long context
    # "gemini-1.5-flash" - Fast model
    # "gemini-2.5-pro" - Latest pro model (if available)
    
    model_name = "gemini-2.5-pro"
    
    start_time = time.time()
    result = evaluate_resume(resume_path, job_description_path, model_name)
    print(f"Time taken: {time.time() - start_time:.2f} seconds")
    
    # # Print formatted JSON
    # print("\n" + "="*50)
    # print("EVALUATION RESULT:")
    # print("="*50)
    # print(json.dumps(result, indent=2))
    
    # Optionally save to file
    with open('evaluation_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nResult saved to evaluation_result.json")


if __name__ == "__main__":
    main()