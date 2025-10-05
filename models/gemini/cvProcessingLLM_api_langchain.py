import pymupdf
from docx import Document
import easyocr
import json
import os
from pathlib import Path
import time
from typing import Dict, Any, List

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain_community.cache import InMemoryCache
from langchain.globals import set_llm_cache
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor

try:
    from prompts import cvscoringPrompt as prompt
    import models.gemini.creds as creds
except:
    from ..prompts import cvscoringPrompt as prompt
    from . import creds

# Enable caching to save API calls
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


# Text extraction functions (same as before)
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


class ResumeEvaluatorLangChain:
    """Enhanced resume evaluator using LangChain with custom prompt"""
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or creds.GOOGLE_API_KEY
        self.model_name = model_name
        
        # Initialize LLM with lower temperature for consistent scoring
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0.1,
            max_retries=3
        )
        
        # Set up output parser
        self.parser = PydanticOutputParser(pydantic_object=ResumeEvaluation)
        
    def create_evaluation_chain(self):
        """Create LangChain evaluation chain with custom prompt"""
        
        # Get the system prompt from your prompts file
        system_prompt = prompt.ast()
        
        template = """{system_prompt}

                    {format_instructions}

                    RESUME:
                    {resume_text}

                    JOB DESCRIPTION:
                    {job_description}

                    Evaluate this resume against the job description following all the criteria above.
                    Return ONLY valid JSON matching the exact format specified. Ensure all scores are integers and total_score equals the sum of all category scores.
                """

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
        
        print("Extracting text from resume...")
        resume_text = extract_resume_text(resume_path)
        
        print("Reading job description...")
        job_description = read_job_description(job_description_path)
        
        print(f"Evaluating with {self.model_name}...")
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
            print(f"Error during evaluation: {e}")
            # Fallback to simpler parsing
            return self._fallback_evaluation(resume_text, job_description)
    
    def _fallback_evaluation(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Fallback evaluation with direct JSON extraction"""
        
        system_prompt = prompt.ast()
        
        simple_prompt = f"""{system_prompt}

                            RESUME:
                            {resume_text}

                            JOB DESCRIPTION:
                            {job_description}

                            Evaluate and return ONLY the JSON output as specified.
                        """

        response = self.llm.predict(simple_prompt)
        
        # Try to extract JSON
        try:
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
        except Exception as e:
            print(f"JSON parsing error: {e}")
        
        return {"error": "Could not parse response", "raw_response": response[:500]}


class ParallelResumeEvaluator:
    """Evaluate different criteria in parallel for faster processing"""
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or creds.GOOGLE_API_KEY
        self.model_name = model_name
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0.1,
            max_retries=2
        )
    
    def evaluate_category(self, category: str, resume_text: str, job_description: str, max_score: int) -> Dict:
        """Evaluate a specific category"""
        
        category_prompts = {
            "education": f"""Evaluate ONLY education (max {max_score} points).
            Guidelines:
            - Base score: Degree match with requirements
            - +1-2: Strong GPA
            - +2-3: Relevant specialization
            - +1-2: Advanced degrees if beneficial
            - Deduct 2-3 if irrelevant, 3-5 if minimum not met

            Resume: {resume_text[:1500]}
            Job: {job_description[:1500]}

            Return JSON: {{"score": <int>, "reason": "<20-30 words>"}}""",

                        "experience": f"""Evaluate ONLY experience (max {max_score} points).
            Guidelines:
            - 0-50% required: 0-5 points
            - 50-75% required: 6-10 points
            - 75-100% required: 11-15 points
            - 100%+ required: 16-20 points
            - Consider role relevance and technical match

            Resume: {resume_text[:1500]}
            Job: {job_description[:1500]}

            Return JSON: {{"score": <int>, "reason": "<20-30 words including years>"}}""",

                        "skills": f"""Evaluate ONLY skills (max {max_score} points).
            Guidelines:
            - Extract required skills from job description
            - Calculate match percentage
            - 90-100% match: 27-30 points
            - 70-89% match: 21-26 points
            - 50-69% match: 15-20 points

            Resume: {resume_text[:2000]}
            Job: {job_description[:2000]}

            Return JSON: {{"score": <int>, "skills_possessed": [], "skills_required": [], "reason": "<20-30 words>"}}"""
        }
        
        prompt_text = category_prompts.get(category, "")
        if not prompt_text:
            return {"score": 0, "reason": "Category not found"}
        
        try:
            response = self.llm.predict(prompt_text)
            return self._extract_json(response)
        except Exception as e:
            print(f"Error evaluating {category}: {e}")
            return {"score": 0, "reason": f"Error: {str(e)[:50]}"}
    
    def _extract_json(self, response: str) -> Dict:
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                return json.loads(response[start_idx:end_idx])
        except:
            pass
        return {}
    
    def evaluate_resume_parallel(self, resume_path: str, job_description_path: str) -> Dict:
        """Evaluate different criteria in parallel - 2-3x faster"""
        
        print("Extracting text...")
        resume_text = extract_resume_text(resume_path)
        job_description = read_job_description(job_description_path)
        
        print("Running parallel evaluation (faster)...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit parallel tasks for main categories
            edu_future = executor.submit(self.evaluate_category, "education", resume_text, job_description, 10)
            exp_future = executor.submit(self.evaluate_category, "experience", resume_text, job_description, 20)
            skills_future = executor.submit(self.evaluate_category, "skills", resume_text, job_description, 30)
            
            # Gather results
            edu_result = edu_future.result()
            exp_result = exp_future.result()
            skills_result = skills_future.result()
        
        # Quick evaluation for remaining categories (lightweight)
        cert_prompt = f"List certifications from resume. Return JSON: {{\"certifications\": []}}\nResume: {resume_text[:1000]}"
        links_prompt = f"Extract all URLs/links from resume. Return JSON: {{\"links\": []}}\nResume: {resume_text[:1000]}"
        projects_prompt = f"List projects from resume. Return JSON: {{\"projects\": []}}\nResume: {resume_text[:1500]}"
        
        cert_data = self._extract_json(self.llm.predict(cert_prompt))
        links_data = self._extract_json(self.llm.predict(links_prompt))
        projects_data = self._extract_json(self.llm.predict(projects_prompt))
        
        # Simple scoring for remaining categories
        cert_score = min(len(cert_data.get('certifications', [])) * 3, 10)
        links_score = min(len(links_data.get('links', [])) * 2, 10)
        projects_score = min(len(projects_data.get('projects', [])) * 7, 20)
        
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
                'certification_list': cert_data.get('certifications', []),
                'reason': f"Found {len(cert_data.get('certifications', []))} certifications"
            },
            'skills': skills_result,
            'active_links': {
                'score': links_score,
                'links': links_data.get('links', []),
                'reason': f"Found {len(links_data.get('links', []))} valid links"
            },
            'projects': {
                'score': projects_score,
                'projects': projects_data.get('projects', []),
                'reason': f"Found {len(projects_data.get('projects', []))} projects"
            },
            'total_score': total_score,
            'overall_assessment': f"Candidate scored {total_score}/100. Education: {edu_result.get('score', 0)}/10, Experience: {exp_result.get('score', 0)}/20, Skills: {skills_result.get('score', 0)}/30.",
            'evaluation_method': 'parallel'
        }


# def main():
#     """Demo of different evaluation approaches"""
    
#     resume_path = "cvs/resume_1.pdf"
#     job_description_path = "jds/jd_1.txt"
    
#     print("\n" + "="*70)
#     print("RESUME EVALUATION SYSTEM - LANGCHAIN ENHANCED")
#     print("="*70)
    
#     # Method 1: Structured LangChain evaluation (More Accurate)
#     print("\n📊 METHOD 1: Structured LangChain Evaluation (Most Accurate)")
#     print("-" * 70)
    
#     start_time = time.time()
#     evaluator = ResumeEvaluatorLangChain(model_name="gemini-2.5-pro")
#     result1 = evaluator.evaluate_resume(resume_path, job_description_path)
#     time1 = time.time() - start_time
    
#     print(f"✅ Completed in: {time1:.2f} seconds")
#     print("\nDetailed Evaluation:")
#     print(json.dumps(result1, indent=2))
    
#     # # Method 2: Parallel evaluation (Faster)
#     # print("\n" + "="*70)
#     # print("⚡ METHOD 2: Parallel Evaluation (2-3x Faster)")
#     # print("-" * 70)
    
#     # start_time = time.time()
#     # parallel_evaluator = ParallelResumeEvaluator(model_name="gemini-2.0-flash-exp")
#     # result2 = parallel_evaluator.evaluate_resume_parallel(resume_path, job_description_path)
#     # time2 = time.time() - start_time
    
#     # print(f"✅ Completed in: {time2:.2f} seconds")
#     # print("\nParallel Evaluation:")
#     # print(json.dumps(result2, indent=2))
    
#     # Save results
#     output = {
#         'structured_evaluation': result1,
#         'performance_metrics': {
#             'structured_time_seconds': round(time1, 2),
#             'recommendation': 'Use structured method for accuracy, parallel for speed'
#         },
#         'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
#     }
    
#     with open('langchain_evaluation.json', 'w') as f:
#         json.dump(output, f, indent=2)
    
#     print("\n" + "="*70)
#     print("📁 Results saved to: langchain_evaluation.json")
#     print("="*70)


# if __name__ == "__main__":
#     main()