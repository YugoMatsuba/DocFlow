"""Unify data models according to plan specifications

Revision ID: 002
Revises: 001
Create Date: 2026-03-19 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update nodes table
    # Add name column
    op.add_column('nodes', sa.Column('name', sa.String(length=255), nullable=False, server_default='Unnamed Node'))

    # Rename config to configuration
    op.alter_column('nodes', 'config', new_column_name='configuration')

    # Rename order_index to order
    op.alter_column('nodes', 'order_index', new_column_name='order')

    # Drop old unique constraint and create new one with updated column name
    op.drop_constraint('uq_workflow_node_order', 'nodes', type_='unique')
    op.create_unique_constraint('uq_workflow_node_order', 'nodes', ['workflow_id', 'order'])

    # Update workflow_executions table
    # Rename input_text to input_file_path and make it nullable
    op.alter_column('workflow_executions', 'input_text', new_column_name='input_file_path', nullable=True)
    op.alter_column('workflow_executions', 'input_file_path', type_=sa.String(length=500), nullable=True)

    # Rename output_text to output_data
    op.alter_column('workflow_executions', 'output_text', new_column_name='output_data')

    # Rename started_at to created_at
    op.alter_column('workflow_executions', 'started_at', new_column_name='created_at')

    # Add updated_at column
    op.add_column('workflow_executions', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # Remove execution_context column
    op.drop_column('workflow_executions', 'execution_context')

    # Update node_type check constraint to use uppercase values
    op.drop_constraint('chk_node_type', 'nodes', type_='check')
    op.create_check_constraint(
        'chk_node_type',
        'nodes',
        sa.text("node_type IN ('EXTRACT_TEXT', 'GENERATIVE_AI', 'FORMATTER')")
    )

    # Update execution status check constraint to use uppercase values and remove cancelled
    op.drop_constraint('chk_execution_status', 'workflow_executions', type_='check')
    op.create_check_constraint(
        'chk_execution_status',
        'workflow_executions',
        sa.text("status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')")
    )

    # Update indexes with new column names
    op.drop_index('idx_nodes_workflow_order', table_name='nodes')
    op.create_index('idx_nodes_workflow_order', 'nodes', ['workflow_id', 'order'])

    op.drop_index('idx_executions_status_started', table_name='workflow_executions')
    op.create_index('idx_executions_status_created', 'workflow_executions', ['status', 'created_at'])


def downgrade() -> None:
    # Reverse all changes in opposite order

    # Revert indexes
    op.drop_index('idx_executions_status_created', table_name='workflow_executions')
    op.create_index('idx_executions_status_started', 'workflow_executions', ['status', 'started_at'])

    op.drop_index('idx_nodes_workflow_order', table_name='nodes')
    op.create_index('idx_nodes_workflow_order', 'nodes', ['workflow_id', 'order_index'])

    # Revert check constraints
    op.drop_constraint('chk_execution_status', 'workflow_executions', type_='check')
    op.create_check_constraint(
        'chk_execution_status',
        'workflow_executions',
        sa.text("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')")
    )

    op.drop_constraint('chk_node_type', 'nodes', type_='check')
    op.create_check_constraint(
        'chk_node_type',
        'nodes',
        sa.text("node_type IN ('extract_text', 'generative_ai', 'formatter')")
    )

    # Revert workflow_executions table changes
    op.add_column('workflow_executions', sa.Column('execution_context', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.drop_column('workflow_executions', 'updated_at')
    op.alter_column('workflow_executions', 'created_at', new_column_name='started_at')
    op.alter_column('workflow_executions', 'output_data', new_column_name='output_text')
    op.alter_column('workflow_executions', 'input_file_path', new_column_name='input_text', type_=sa.Text(), nullable=False)

    # Revert nodes table changes
    op.drop_constraint('uq_workflow_node_order', 'nodes', type_='unique')
    op.create_unique_constraint('uq_workflow_node_order', 'nodes', ['workflow_id', 'order_index'])
    op.alter_column('nodes', 'order', new_column_name='order_index')
    op.alter_column('nodes', 'configuration', new_column_name='config')
    op.drop_column('nodes', 'name')