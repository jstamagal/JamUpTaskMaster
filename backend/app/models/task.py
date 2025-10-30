from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Task(Base):
    """Task model - keeps it simple, no rigid structure"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    raw_input = Column(Text, nullable=False)  # What you actually typed
    processed_text = Column(Text, nullable=True)  # What the secretary understood
    status = Column(String, default="captured")  # captured, active, done, archived
    priority_score = Column(Float, default=0.5)  # 0-1, assessed by prioritizer
    category = Column(String, nullable=True)  # Assigned by organizer
    notes = Column(Text, nullable=True)  # LLM-generated context

    # Time stuff - loose, not rigid
    created_at = Column(DateTime, default=datetime.utcnow)
    touched_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_by = Column(DateTime, nullable=True)  # Optional, only if you specify
    recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # "daily", "every 2 days", etc

    # Flags
    is_life_critical = Column(Boolean, default=False)  # Meds, food, basics
    is_interesting = Column(Boolean, default=False)  # Fun stuff that pulls focus
    is_quick_win = Column(Boolean, default=False)  # Can knock out fast

    def to_dict(self):
        return {
            "id": self.id,
            "raw_input": self.raw_input,
            "processed_text": self.processed_text,
            "status": self.status,
            "priority_score": self.priority_score,
            "category": self.category,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "touched_at": self.touched_at.isoformat() if self.touched_at else None,
            "due_by": self.due_by.isoformat() if self.due_by else None,
            "recurring": self.recurring,
            "recurring_pattern": self.recurring_pattern,
            "is_life_critical": self.is_life_critical,
            "is_interesting": self.is_interesting,
            "is_quick_win": self.is_quick_win,
        }
