from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    root_dir = Column(String(500), nullable=False)
    docker_network = Column(String(100), nullable=False)
    port_range_start = Column(Integer, nullable=False)
    port_range_end = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    instances = relationship("Instance", back_populates="group", cascade="all, delete-orphan")

class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("groups.id"), nullable=False)
    name = Column(String(100), nullable=False)
    container_name = Column(String(100), nullable=False, unique=True)
    host_port = Column(Integer, nullable=False)
    status = Column(String(20), default="stopped") # running, stopped, removed
    created_at = Column(DateTime, default=datetime.utcnow)
    config_snapshot = Column(Text, nullable=True) # JSON snapshot of config
    
    group = relationship("Group", back_populates="instances")

DATABASE_URL = "sqlite:///./data/openclaw.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
