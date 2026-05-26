from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id          = Column(Integer, primary_key=True)
    name        = Column(String, unique=True, nullable=False)
    description = Column(String)
    system      = Column(Text, nullable=False)
    user_prefix = Column(Text, default="")
    user_suffix = Column(Text, default="")
    model       = Column(String, default="llama3")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())