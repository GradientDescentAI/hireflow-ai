from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBJob(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    schema_json = Column(JSON)  # JobDescription schema
    status = Column(String, default="draft")

class DBCandidateProfile(Base):
    __tablename__ = "candidates"
    id = Column(String, primary_key=True, index=True)
    jd_id = Column(String, index=True)
    schema_json = Column(JSON)

class DBCandidateScore(Base):
    __tablename__ = "scores"
    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, index=True)
    jd_id = Column(String, index=True)
    schema_json = Column(JSON)

Base.metadata.create_all(bind=engine)
