"""Initial schema with workflows, nodes, and workflow_executions tables

Revision ID: 001
Revises:
Create Date: 2026-03-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workflow_id', sa.String(), nullable=False),
        sa.Column('node_type', sa.String(), nullable=False),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=False, default=dict),
        sa.Column('order_index', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'order_index', name='uq_workflow_node_order')
    )

    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workflow_id', sa.String(), nullable=False),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('output_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_context', postgresql.JSON(astext_type=sa.Text()), nullable=False, default=dict),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better performance
    op.create_index('idx_workflows_created', 'workflows', ['created_at'])
    op.create_index('idx_nodes_workflow_order', 'nodes', ['workflow_id', 'order_index'])
    op.create_index('idx_executions_workflow_status', 'workflow_executions', ['workflow_id', 'status'])
    op.create_index('idx_executions_status_started', 'workflow_executions', ['status', 'started_at'])

    # Add check constraints for enum-like values
    op.create_check_constraint(
        'chk_node_type',
        'nodes',
        sa.text("node_type IN ('extract_text', 'generative_ai', 'formatter')")
    )

    op.create_check_constraint(
        'chk_execution_status',
        'workflow_executions',
        sa.text("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')")
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_executions_status_started', table_name='workflow_executions')
    op.drop_index('idx_executions_workflow_status', table_name='workflow_executions')
    op.drop_index('idx_nodes_workflow_order', table_name='nodes')
    op.drop_index('idx_workflows_created', table_name='workflows')

    # Drop check constraints
    op.drop_constraint('chk_execution_status', 'workflow_executions', type_='check')
    op.drop_constraint('chk_node_type', 'nodes', type_='check')

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('workflow_executions')
    op.drop_table('nodes')
    op.drop_table('workflows')