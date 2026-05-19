from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy import Boolean, Text, DateTime, JSON, LargeBinary, func
from app.db.database import Base

class Config(Base):
    __tablename__ = "configs"
    id          = Column(Integer, primary_key=True)
    customer_id = Column(String, nullable=False)
    key         = Column(String, nullable=False)
    value       = Column(LargeBinary)   # AES-256 encrypted
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

class RagChunk(Base):
    __tablename__ = "rag_chunks"
    id           = Column(Integer, primary_key=True)
    customer_id  = Column(String, nullable=False)
    doc_name     = Column(String, nullable=False)
    chunk_index  = Column(Integer, nullable=False)
    content      = Column(Text, nullable=False)
    embedding_id = Column(String)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

class License(Base):
    __tablename__ = "licenses"
    id           = Column(Integer, primary_key=True)
    license_key  = Column(String, unique=True, nullable=False)
    machine_id   = Column(String)
    plan         = Column(String, default="starter")
    activated_at = Column(DateTime(timezone=True))
    expires_at   = Column(DateTime(timezone=True))
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

class UsageLog(Base):
    __tablename__ = "usage_logs"
    id           = Column(BigInteger, primary_key=True)
    customer_id  = Column(String, nullable=False)
    event_type   = Column(String, nullable=False)
    event_data   = Column(JSON)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())