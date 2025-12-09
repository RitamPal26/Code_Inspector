"""
SQLAlchemy database models for workflow engine.

This module defines the database schema using SQLAlchemy ORM with async support.
All models use PostgreSQL-specific types (UUID, JSONB) for optimal performance.
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from typing import Any

Base = declarative_base()

class Workflow(Base):
    
    __tablename__ = "workflows"
    
    id: UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    name: str = Column(
        String(255),
        nullable=False,
        index=True
    )
    description: str | None = Column(
        Text,
        nullable=True
    )
    graph_definition: dict[str, Any] = Column(
        JSONB,
        nullable=False
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: datetime | None = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        """String representation of Workflow."""
        return f"<Workflow(id={self.id}, name='{self.name}')>"

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    
    run_id: UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    workflow_id: UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: str = Column(
        String(50),
        nullable=False,
        index=True
    )
    current_node: str | None = Column(
        String(255),
        nullable=True
    )
    current_state: dict[str, Any] | None = Column(
        JSONB,
        nullable=True
    )
    iteration_count: int = Column(
        Integer,
        default=0,
        nullable=False
    )
    execution_logs: list[dict[str, Any]] = Column(
        JSONB,
        default=list,
        nullable=False
    )
    error_message: str | None = Column(
        Text,
        nullable=True
    )
    started_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: datetime | None = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    __table_args__ = (
        Index("idx_workflow_runs_status_created", "status", "started_at"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowRun(run_id={self.run_id}, status='{self.status}')>"
