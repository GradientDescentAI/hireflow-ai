from langchain_google_genai import ChatGoogleGenerativeAI
from models.schemas import JobDescription
from core.config import settings

def extract_job_description(raw_jd: str) -> JobDescription:
    """
    Takes a raw JD text, and asks the LLM (Gemini) to extract it
    into the JobDescription Pydantic schema using structured output.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        temperature=0,
        google_api_key=settings.GEMINI_API_KEY
    )
    
    structured_llm = llm.with_structured_output(JobDescription)
    
    # In a real app, job description IDs could be passed in or generated upstream
    prompt = f"Convert the following Job Description into the strictly defined structured Schema. You must generate a unique ID for 'id'.\n\n{raw_jd}"
    result = structured_llm.invoke(prompt)
    return result
