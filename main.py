from models.gemini.cvProcessingLLM_api_langchain import ResumeEvaluatorLangChain 
from models.gemini import avilableModels as geminimodellist

import time
import json

def test_model():
    
    resume_path = "cvs/resume_1.pdf"
    job_description_path = "jds/jd_1.txt"
    model_name = "gemini-2.5-pro"
    
    print("\n" + "="*70)
    print("RESUME EVALUATION SYSTEM - LANGCHAIN ENHANCED")
    print("="*70)
    
    # Method 1: Structured LangChain evaluation (More Accurate)
    print("\n📊 METHOD 1: Structured LangChain Evaluation (Most Accurate)")
    print("-" * 70)
    
    start_time = time.time()
    evaluator = ResumeEvaluatorLangChain(model_name=model_name)
    result1 = evaluator.evaluate_resume(resume_path, job_description_path)
    time1 = time.time() - start_time
    
    print(f"✅ Completed in: {time1:.2f} seconds")
    print("\nDetailed Evaluation:")
    print(json.dumps(result1, indent=2))
    
    # Save results
    output = {
        'structured_evaluation': result1,
        'performance_metrics': {
            'structured_time_seconds': round(time1, 2),
            'recommendation': 'Use structured method for accuracy, parallel for speed'
        },
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('langchain_evaluation.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "="*70)
    print("📁 Results saved to: langchain_evaluation.json")
    print("="*70)


def test_list():
    modles = geminimodellist.gemini_models
    print(modles)


if __name__ == "__main__":
    test_list()