from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn

DATABASE_URL = "sqlite:///./glossary.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Term(Base):
    __tablename__ = "terms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# схемы
class TermBase(BaseModel):
    name: str
    description: str

class TermCreate(TermBase):
    pass

class TermUpdate(BaseModel):
    description: str

class TermOut(TermBase):
    id: int

    class Config:
        orm_mode = True

app = FastAPI(title="Glossary API", description="A simple glossary API using FastAPI.", version="1.0.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# роуты
@app.get("/terms", response_model=list[TermOut])
def get_terms(db: Session = Depends(get_db)):
    return db.query(Term).all()

@app.get("/terms/{name}", response_model=TermOut)
def get_term(name: str, db: Session = Depends(get_db)):
    term = db.query(Term).filter(Term.name == name).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term

@app.post("/terms", response_model=TermOut, status_code=201)
def create_term(term: TermCreate, db: Session = Depends(get_db)):
    existing_term = db.query(Term).filter(Term.name == term.name).first()
    if existing_term:
        raise HTTPException(status_code=400, detail="Term already exists")
    new_term = Term(name=term.name, description=term.description)
    db.add(new_term)
    db.commit()
    db.refresh(new_term)
    return new_term

@app.put("/terms/{name}", response_model=TermOut)
def update_term(name: str, update: TermUpdate, db: Session = Depends(get_db)):
    term = db.query(Term).filter(Term.name == name).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    term.description = update.description
    db.commit()
    db.refresh(term)
    return term

@app.delete("/terms/{name}", status_code=204)
def delete_term(name: str, db: Session = Depends(get_db)):
    term = db.query(Term).filter(Term.name == name).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    db.delete(term)
    db.commit()
    return {"message": "Term deleted"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
