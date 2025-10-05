import pymupdf
from docx import Document
import easyocr
import json
import os
from pathlib import Path
import time
from typing import Dict, Any, List
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor

try:
    from prompts import cvscoringPrompt as prompt
    import models.gemini.creds as creds
except:
    from ..prompts import cvscoringPrompt as prompt
    from ..gemini import creds

# Enable caching to save processing time
set_llm_cache(InMemoryCache())


# Define structured output schemas matching the prompt format
class ScoreDetail(BaseModel):
    score: int = Field(description="Score for this category")
    reason: str = Field(description="Detailed explanation for the score")

class CertificationDetail(BaseModel):
    score: int = Field(description="Certification score out of 10")
    certification_list: List[str] = Field(description="List of certifications found")
    reason: str = Field(description="Explanation of certification relevance")

class SkillsDetail(BaseModel):
    score: int = Field(description="Skills score out of 30")
    skills_possessed: List[str] = Field(description="Skills the candidate has")
    skills_required: List[str] = Field(description="Skills required for the job")
    reason: str = Field(description="Explanation of skill match percentage")

class ActiveLinksDetail(BaseModel):
    score: int = Field(description="Active links score out of 10")
    links: List[str] = Field(description="List of valid links found")
    reason: str = Field(description="Explanation of link scoring")

class ProjectsDetail(BaseModel):
    score: int = Field(description="Projects score out of 20")
    projects: List[str] = Field(description="List of projects")
    reason: str = Field(description="Assessment of project complexity and relevance")

class ResumeEvaluation(BaseModel):
    name: str = Field(description="Candidate name", default="")
    email: str = Field(description="Candidate email", default="")
    phone: str = Field(description="Candidate phone", default="")
    profile: str = Field(description="Candidate profile summary", default="")
    bio: str = Field(description="Candidate bio", default="")
    education: ScoreDetail = Field(description="Education evaluation")
    experience: ScoreDetail = Field(description="Experience evaluation")
    certifications: CertificationDetail = Field(description="Certifications evaluation")
    skills: SkillsDetail = Field(description="Skills evaluation")
    active_links: ActiveLinksDetail = Field(description="Active links evaluation")
    projects: ProjectsDetail = Field(description="Projects evaluation")
    total_score: int = Field(description="Sum of all scores", ge=0, le=100)
    overall_assessment: str = Field(description="Detailed summary of candidate evaluation")


# Text extraction functions
def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def extract_text_from_doc(doc_path):
    try:
        return extract_text_from_docx(doc_path)
    except Exception as e:
        print(f"Warning: Could not extract from .doc file: {e}")
        return ""


def extract_text_from_image(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    text = " ".join([detection[1] for detection in result])
    return text


def extract_resume_text(resume_path):
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
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()


class ResumeEvaluatorOllama:
    """Resume evaluator using Ollama Llama2"""
    
    def __init__(self, model_name: str = "llama2:7b", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama evaluator
        
        Args:
            model_name: Ollama model name (default: "llama2:7b")
                       Other options: "llama2:13b", "llama2:70b", "mistral", "mixtral"
            base_url: Ollama server URL (default: "http://localhost:11434")
        """
        self.model_name = model_name
        self.base_url = base_url
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            temperature=0.1,  # Lower temperature for consistent scoring
            num_predict=2048,  # Max tokens to generate
            top_p=0.9,
            repeat_penalty=1.1
        )
        
        # Set up output parser
        self.parser = PydanticOutputParser(pydantic_object=ResumeEvaluation)
        
        print(f"✅ Initialized Ollama with model: {model_name}")
        print(f"📍 Server: {base_url}")
        
    def create_evaluation_chain(self):
        """Create LangChain evaluation chain with custom prompt"""
        
        # Get the system prompt from your prompts file
        system_prompt = prompt.ast()
        
        template = """{system_prompt}

IMPORTANT: You must respond with ONLY valid JSON. No additional text before or after the JSON.

{format_instructions}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Evaluate this resume against the job description following all the criteria above.
Return ONLY valid JSON matching the exact format specified. Ensure all scores are integers and total_score equals the sum of all category scores.

JSON OUTPUT:"""

        prompt_template = PromptTemplate(
            template=template,
            input_variables=["resume_text", "job_description"],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions(),
                "system_prompt": system_prompt
            }
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        return chain
    
    def evaluate_resume(self, resume_path: str, job_description_path: str) -> Dict[str, Any]:
        """Evaluate resume with structured output"""
        
        print("\n📄 Extracting text from resume...")
        resume_text = extract_resume_text(resume_path)
        
        print("📋 Reading job description...")
        job_description = read_job_description(job_description_path)
        
        # Truncate if too long for Llama2 context window
        if len(resume_text) > 2000:
            print("⚠️  Resume text truncated to fit context window")
            resume_text = resume_text[:2000]
        if len(job_description) > 1500:
            print("⚠️  Job description truncated to fit context window")
            job_description = job_description[:1500]
        
        print(f"🤖 Evaluating with Ollama {self.model_name}...")
        print("⏳ This may take 30-60 seconds with Llama2...")
        
        chain = self.create_evaluation_chain()
        
        try:
            response = chain.run(
                resume_text=resume_text,
                job_description=job_description
            )
            
            # Parse the response using Pydantic
            result = self.parser.parse(response)
            
            # Validate total score
            calculated_total = (
                result.education.score +
                result.experience.score +
                result.certifications.score +
                result.skills.score +
                result.active_links.score +
                result.projects.score
            )
            
            if result.total_score != calculated_total:
                print(f"⚠️ Warning: Total score mismatch. Calculated: {calculated_total}, Reported: {result.total_score}")
                result.total_score = calculated_total
            
            return result.dict()
            
        except Exception as e:
            print(f"❌ Error during structured parsing: {e}")
            print("🔄 Attempting fallback evaluation...")
            # Fallback to simpler parsing
            return self._fallback_evaluation(resume_text, job_description)
    
    def _fallback_evaluation(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Fallback evaluation with direct JSON extraction"""
        
        system_prompt = prompt.ast()
        
        simple_prompt = f"""{system_prompt}

RESUME:
{resume_text[:2000]}

JOB DESCRIPTION:
{job_description[:1500]}

Evaluate and return ONLY the JSON output as specified. Start your response with {{ and end with }}. No other text."""

        print("🔄 Running fallback evaluation...")
        response = self.llm.predict(simple_prompt)
        
        # Try to extract JSON
        try:
            # Find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate total score
                calculated_total = (
                    result.get('education', {}).get('score', 0) +
                    result.get('experience', {}).get('score', 0) +
                    result.get('certifications', {}).get('score', 0) +
                    result.get('skills', {}).get('score', 0) +
                    result.get('active_links', {}).get('score', 0) +
                    result.get('projects', {}).get('score', 0)
                )
                
                result['total_score'] = calculated_total
                return result
            else:
                print("❌ Could not find JSON in response")
                return self._create_basic_evaluation(resume_text, job_description)
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return self._create_basic_evaluation(resume_text, job_description)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {"error": "Could not parse response", "raw_response": response[:500]}
    
    def _create_basic_evaluation(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Create a basic evaluation when JSON parsing fails"""
        
        print("⚠️  Creating basic rule-based evaluation...")
        
        # Simple keyword matching for basic score
        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()
        
        # Basic scoring logic
        edu_score = 5 if any(word in resume_lower for word in ['bachelor', 'master', 'phd', 'degree']) else 3
        exp_score = 10  # Default mid-range
        cert_score = 3 if any(word in resume_lower for word in ['certified', 'certification']) else 0
        
        # Extract some basic info
        name = "Not extracted"
        email = "Not extracted"
        
        return {
            "name": name,
            "email": email,
            "phone": "",
            "profile": "",
            "bio": "",
            "education": {"score": edu_score, "reason": "Basic extraction due to parsing issues"},
            "experience": {"score": exp_score, "reason": "Default scoring applied"},
            "certifications": {"score": cert_score, "certification_list": [], "reason": "Limited extraction"},
            "skills": {"score": 15, "skills_possessed": [], "skills_required": [], "reason": "Partial matching"},
            "active_links": {"score": 0, "links": [], "reason": "Not extracted"},
            "projects": {"score": 5, "projects": [], "reason": "Basic estimation"},
            "total_score": edu_score + exp_score + cert_score + 15 + 5,
            "overall_assessment": "Basic evaluation performed due to parsing limitations with local LLM.",
            "note": "Consider using a larger model or adjusting prompt for better results"
        }


class ParallelResumeEvaluatorOllama:
    """Evaluate different criteria in parallel using Ollama"""
    
    def __init__(self, model_name: str = "llama2:7b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            temperature=0.1,
            num_predict=512,  # Shorter responses for speed
            top_p=0.9
        )
        print(f"✅ Initialized parallel evaluator with {model_name}")
    
    def evaluate_category(self, category: str, resume_text: str, job_description: str, max_score: int) -> Dict:
        """Evaluate a specific category"""
        
        category_prompts = {
            "education": f"""Evaluate ONLY education level (max {max_score} points).
Consider: degree type, GPA, relevant specialization, advanced degrees.
Deduct if irrelevant or minimum not met.

Resume (excerpt): {resume_text[:800]}
Job Requirements: {job_description[:500]}

Return ONLY this JSON format:
{{"score": <integer 0-{max_score}>, "reason": "<explanation in 20-30 words>"}}""",

            "experience": f"""Evaluate ONLY work experience (max {max_score} points).
Score based on years and relevance:
0-50% of required: 0-5 pts, 50-75%: 6-10 pts, 75-100%: 11-15 pts, 100%+: 16-20 pts

Resume (excerpt): {resume_text[:800]}
Job Requirements: {job_description[:500]}

Return ONLY this JSON format:
{{"score": <integer 0-{max_score}>, "reason": "<explanation with years in 20-30 words>"}}""",

            "skills": f"""Evaluate ONLY technical/soft skills match (max {max_score} points).
Calculate match percentage: 90-100%: 27-30 pts, 70-89%: 21-26 pts, 50-69%: 15-20 pts

Resume (excerpt): {resume_text[:1000]}
Job Requirements: {job_description[:800]}

Return ONLY this JSON format:
{{"score": <integer 0-{max_score}>, "skills_possessed": ["skill1", "skill2"], "skills_required": ["req1", "req2"], "reason": "<match % in 20-30 words>"}}"""
        }
        
        prompt_text = category_prompts.get(category, "")
        if not prompt_text:
            return {"score": 0, "reason": "Category not found"}
        
        try:
            response = self.llm.predict(prompt_text)
            return self._extract_json(response)
        except Exception as e:
            print(f"⚠️  Error evaluating {category}: {e}")
            return {"score": 0, "reason": f"Error in evaluation"}
    
    def _extract_json(self, response: str) -> Dict:
        """Extract JSON from response"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            print(f"⚠️  JSON extraction error: {e}")
        return {}
    
    def evaluate_resume_parallel(self, resume_path: str, job_description_path: str) -> Dict:
        """Evaluate different criteria in parallel"""
        
        print("\n📄 Extracting text...")
        resume_text = extract_resume_text(resume_path)
        job_description = read_job_description(job_description_path)
        
        print("⚡ Running parallel evaluation with Ollama...")
        print("⏳ Processing 3 categories simultaneously...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit parallel tasks for main categories
            edu_future = executor.submit(self.evaluate_category, "education", resume_text, job_description, 10)
            exp_future = executor.submit(self.evaluate_category, "experience", resume_text, job_description, 20)
            skills_future = executor.submit(self.evaluate_category, "skills", resume_text, job_description, 30)
            
            # Gather results
            edu_result = edu_future.result()
            exp_result = exp_future.result()
            skills_result = skills_future.result()
        
        print("📊 Extracting remaining information...")
        
        # Quick evaluation for remaining categories
        cert_prompt = f"Extract certifications from this resume. Return JSON: {{\"certifications\": [\"cert1\", \"cert2\"]}}\n\nResume: {resume_text[:1000]}"
        links_prompt = f"Extract all URLs and links from this resume. Return JSON: {{\"links\": [\"url1\", \"url2\"]}}\n\nResume: {resume_text[:800]}"
        projects_prompt = f"Extract project names from this resume. Return JSON: {{\"projects\": [\"project1\", \"project2\"]}}\n\nResume: {resume_text[:1200]}"
        
        cert_data = self._extract_json(self.llm.predict(cert_prompt))
        links_data = self._extract_json(self.llm.predict(links_prompt))
        projects_data = self._extract_json(self.llm.predict(projects_prompt))
        
        # Simple scoring for remaining categories
        certs = cert_data.get('certifications', [])
        links = links_data.get('links', [])
        projects = projects_data.get('projects', [])
        
        cert_score = min(len(certs) * 3, 10)
        links_score = min(len(links) * 2, 10)
        projects_score = min(len(projects) * 7, 20)
        
        total_score = (
            edu_result.get('score', 0) +
            exp_result.get('score', 0) +
            cert_score +
            skills_result.get('score', 0) +
            links_score +
            projects_score
        )
        
        return {
            'education': edu_result,
            'experience': exp_result,
            'certifications': {
                'score': cert_score,
                'certification_list': certs,
                'reason': f"Found {len(certs)} certification(s)"
            },
            'skills': skills_result,
            'active_links': {
                'score': links_score,
                'links': links,
                'reason': f"Found {len(links)} active link(s)"
            },
            'projects': {
                'score': projects_score,
                'projects': projects,
                'reason': f"Found {len(projects)} project(s)"
            },
            'total_score': total_score,
            'overall_assessment': f"Candidate scored {total_score}/100. Education: {edu_result.get('score', 0)}/10, Experience: {exp_result.get('score', 0)}/20, Skills: {skills_result.get('score', 0)}/30. Evaluated using Ollama {self.model_name}.",
            'evaluation_method': 'parallel_ollama',
            'model_used': self.model_name
        }


# def main():
#     """Demo of Ollama evaluation approaches"""
    
#     resume_path = "cvs/resume_1.pdf"
#     job_description_path = "jds/jd_1.txt"
    
#     print("\n" + "="*70)
#     print("RESUME EVALUATION SYSTEM - OLLAMA LLAMA2")
#     print("="*70)
#     print("\n⚠️  PREREQUISITES:")
#     print("1. Install Ollama: https://ollama.ai")
#     print("2. Pull model: ollama pull llama2:7b")
#     print("3. Ensure Ollama is running: ollama serve")
#     print("="*70)
    
#     # Check which method to use
#     evaluation_method = input("\nChoose method:\n1. Structured (Slower, More Detailed)\n2. Parallel (Faster)\nEnter 1 or 2: ").strip()
    
#     if evaluation_method == "1":
#         # Method 1: Structured evaluation
#         print("\n📊 METHOD 1: Structured Ollama Evaluation")
#         print("-" * 70)
        
#         start_time = time.time()
#         evaluator = ResumeEvaluatorOllama(model_name="gemma3:4b")
#         result = evaluator.evaluate_resume(resume_path, job_description_path)
#         time_taken = time.time() - start_time
        
#         print(f"\n✅ Completed in: {time_taken:.2f} seconds")
#         print("\nDetailed Evaluation:")
#         print(json.dumps(result, indent=2))
        
#         # Save result
#         with open('ollama_evaluation.json', 'w') as f:
#             json.dump(result, f, indent=2)
        
#     else:
#         # Method 2: Parallel evaluation
#         print("\n⚡ METHOD 2: Parallel Ollama Evaluation")
#         print("-" * 70)
        
#         start_time = time.time()
#         parallel_evaluator = ParallelResumeEvaluatorOllama(model_name="llama2:7b")
#         result = parallel_evaluator.evaluate_resume_parallel(resume_path, job_description_path)
#         time_taken = time.time() - start_time
        
#         print(f"\n✅ Completed in: {time_taken:.2f} seconds")
#         print("\nParallel Evaluation:")
#         print(json.dumps(result, indent=2))
        
#         # Save result
#         with open('ollama_evaluation_parallel.json', 'w') as f:
#             json.dump(result, f, indent=2)
    
#     print("\n" + "="*70)
#     print("📁 Results saved!")
#     print("="*70)
    
#     print("\n💡 TIPS:")
#     print("- Llama2:7b is faster but less accurate than larger models")
#     print("- Try 'llama2:13b' or 'mistral' for better results")
#     print("- Use parallel method for batch processing")
#     print("- Structured method provides more detailed output")


# if __name__ == "__main__":
#     main()