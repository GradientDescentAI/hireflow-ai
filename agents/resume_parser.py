from langchain_google_genai import ChatGoogleGenerativeAI
from models.schemas import CandidateProfile
from core.config import settings
from pypdf import PdfReader
import io

def parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_candidate_profile(pdf_bytes: bytes, jd_id: str) -> CandidateProfile:
    raw_text = parse_pdf(pdf_bytes)
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=settings.GEMINI_API_KEY
    )
    
    structured_llm = llm.with_structured_output(CandidateProfile)
    
    prompt = f"Extract the following Resume text into the Candidate Profile Schema. Use '{jd_id}' for the jd_id field:\n\n{raw_text}"
    return structured_llm.invoke(prompt)
