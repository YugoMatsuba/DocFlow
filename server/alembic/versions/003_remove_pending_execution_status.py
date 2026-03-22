"""Remove pending execution status

Revision ID: 003
Revises: 002
Create Date: 2026-03-21 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Normalize any legacy pending rows before tightening the constraint.
    op.execute("UPDATE workflow_executions SET status = 'RUNNING' WHERE status = 'PENDING'")

    op.drop_constraint('chk_execution_status', 'workflow_executions', type_='check')
    op.create_check_constraint(
        'chk_execution_status',
        'workflow_executions',
        sa.text("status IN ('RUNNING', 'COMPLETED', 'FAILED')")
    )


def downgrade() -> None:
    op.drop_constraint('chk_execution_status', 'workflow_executions', type_='check')
    op.create_check_constraint(
        'chk_execution_status',
        'workflow_executions',
        sa.text("status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')")
    )
