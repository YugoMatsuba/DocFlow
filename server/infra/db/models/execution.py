from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base import Base

class WorkflowExecutionModel(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False
    )
    input_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    output_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    workflow: Mapped["WorkflowModel"] = relationship("WorkflowModel", back_populates="executions")

    def __repr__(self):
        return f"<WorkflowExecutionModel(id={self.id}, status={self.status})>"