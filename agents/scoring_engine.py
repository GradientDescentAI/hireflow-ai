from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings
from models.schemas import JobDescription, CandidateProfile, CandidateScore

def score_candidate(jd: JobDescription, profile: CandidateProfile) -> CandidateScore:
    """
    Scores the parsed candidate profile against the JD requirements perfectly deterministically.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0, # Deterministic scoring
        google_api_key=settings.GEMINI_API_KEY
    )
    
    structured_llm = llm.with_structured_output(CandidateScore)
    
    prompt = f"""
    You are an expert AI recruitment evaluator.
    Evaluate the following Candidate Profile against the provided Job Description.
    
    Job Description: {jd.model_dump_json(indent=2)}
    
    Candidate Profile: {profile.model_dump_json(indent=2)}
    
    You must output a highly structured CandidateScore object based on the matching and scoring rubric (out of 100).
    Provide actionable strength points, risk factors, and clear justifications.
    Ensure "candidate_id" and "jd_id" match the objects appropriately. 
    Use "gemini-1.5-flash" for model_version.
    If the candidate is extremely close but misses 1 mandatory requirement, flag near_miss_flag=True.
    """
    
    return structured_llm.invoke(prompt)
