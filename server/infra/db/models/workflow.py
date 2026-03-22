from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, Integer, JSON, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base import Base

class WorkflowModel(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    nodes: Mapped[List["NodeModel"]] = relationship(
        "NodeModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="NodeModel.order"
    )
    executions: Mapped[List["WorkflowExecutionModel"]] = relationship(
        "WorkflowExecutionModel",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<WorkflowModel(id={self.id}, name={self.name})>"

class NodeModel(Base):
    __tablename__ = "nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False
    )
    node_type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    workflow: Mapped["WorkflowModel"] = relationship("WorkflowModel", back_populates="nodes")

    # Constraints
    __table_args__ = (
        UniqueConstraint('workflow_id', 'order', name='uq_workflow_node_order'),
    )

    def __repr__(self):
        return f"<NodeModel(id={self.id}, name='{self.name}', type={self.node_type}, order={self.order})>"