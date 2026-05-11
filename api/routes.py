from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import datetime

from models.database import SessionLocal, DBJob, DBCandidateProfile, DBCandidateScore
from models.schemas import JobDescription, CandidateProfile, CandidateScore
from agents.jd_intake import extract_job_description
from agents.resume_parser import extract_candidate_profile
from agents.distribution import generate_linkedin_post, post_to_linkedin
from agents.scoring_engine import score_candidate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class JDInput(BaseModel):
    jd_text: str

@router.post("/jobs", response_model=JobDescription)
def create_job(input_data: JDInput, db: Session = Depends(get_db)):
    """Triggers JD Intake Agent to build structured profile"""
    try:
        jd_schema = extract_job_description(input_data.jd_text)
        # Ensure it has an ID
        if not jd_schema.id:
            jd_schema.id = str(uuid.uuid4())
            
        db_job = DBJob(id=jd_schema.id, schema_json=jd_schema.model_dump(), status="draft")
        db.add(db_job)
        db.commit()
        return jd_schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/jobs/{job_id}/publish")
def publish_job(job_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers linkedin distribution agent"""
    db_job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    jd = JobDescription(**db_job.schema_json)
    try:
        post_content = generate_linkedin_post(jd)
        # Launch playwright in the background to not block the API
        background_tasks.add_task(post_to_linkedin, post_content)
        
        db_job.status = "posted"
        db.commit()
        return {"status": "Posting initiated", "preview_content": post_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/jobs/{job_id}/applications", response_model=CandidateProfile)
async def upload_application(job_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Manual upload endpoint -> Triggers parsing agent"""
    db_job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    contents = await file.read()
    try:
        profile = extract_candidate_profile(contents, job_id)
        if not profile.id:
            profile.id = str(uuid.uuid4())
            
        db_profile = DBCandidateProfile(id=profile.id, jd_id=job_id, schema_json=profile.model_dump())
        db.add(db_profile)
        db.commit()
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/score")
def run_scoring(job_id: str, db: Session = Depends(get_db)):
    """Batch scores all un-scored applicants against JD"""
    db_job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    jd = JobDescription(**db_job.schema_json)
    
    # Get all candidates for JD
    db_candidates = db.query(DBCandidateProfile).filter(DBCandidateProfile.jd_id == job_id).all()
    
    # Get all existing scores to avoid double processing
    existing_scores = db.query(DBCandidateScore).filter(DBCandidateScore.jd_id == job_id).all()
    scored_ids = {s.candidate_id for s in existing_scores}
    
    results = []
    
    for db_cand in db_candidates:
        if db_cand.id in scored_ids:
            continue
            
        profile = CandidateProfile(**db_cand.schema_json)
        try:
            score = score_candidate(jd, profile)
            if not score.id:
                score.id = str(uuid.uuid4())
            score.candidate_id = profile.id
            score.jd_id = jd.id
            score.scored_at = datetime.datetime.now().isoformat()
            
            db_score = DBCandidateScore(
                id=score.id, 
                candidate_id=profile.id, 
                jd_id=job_id, 
                schema_json=score.model_dump()
            )
            db.add(db_score)
            results.append(score.model_dump())
        except Exception as e:
             # Real system would queue and log
             print(f"Failed to score {profile.id}: {e}")
             
    db.commit()
    return {"scored_count": len(results), "new_scores": results}
