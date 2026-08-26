"""Optimize Database Indexes for Performance (Épic 8)

Revision ID: 20260826_0004
Revises: 20260825_0003
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260826_0004'
down_revision = '20260825_0003'
branch_labels = None
depends_on = None


def upgrade():
    """Create recommended indexes for performance optimization (Épic 8)."""
    
    # Indexes for agents table
    # Note: name already has a unique constraint, but we explicitly create the index for clarity
    op.create_index('idx_agents_name', 'agents', ['name'], unique=True)
    op.create_index('idx_agents_is_active', 'agents', ['is_active'])
    op.create_index('idx_agents_created_at', 'agents', ['created_at'])
    op.create_index('idx_agents_created_by', 'agents', ['created_by'])
    op.create_index('idx_agents_project_id', 'agents', ['project_id'])
    op.create_index('idx_agents_model', 'agents', ['model'])
    op.create_index('idx_agents_is_active_created_at', 'agents', ['is_active', 'created_at'])
    
    # Indexes for executions table
    op.create_index('idx_executions_agent_id', 'executions', ['agent_id'])
    op.create_index('idx_executions_status', 'executions', ['status'])
    op.create_index('idx_executions_created_at', 'executions', ['created_at'])
    op.create_index('idx_executions_executed_by', 'executions', ['executed_by'])
    op.create_index('idx_executions_workflow_id', 'executions', ['workflow_id'])
    op.create_index('idx_executions_model_used', 'executions', ['model_used'])
    op.create_index('idx_executions_agent_id_created_at', 'executions', ['agent_id', 'created_at'])
    op.create_index('idx_executions_status_created_at', 'executions', ['status', 'created_at'])
    op.create_index('idx_executions_started_at', 'executions', ['started_at'])
    op.create_index('idx_executions_completed_at', 'executions', ['completed_at'])
    
    # Indexes for generated_files table
    op.create_index('idx_generated_files_agent_id', 'generated_files', ['agent_id'])
    op.create_index('idx_generated_files_execution_id', 'generated_files', ['execution_id'])
    op.create_index('idx_generated_files_created_at', 'generated_files', ['created_at'])
    op.create_index('idx_generated_files_file_format', 'generated_files', ['file_format'])
    op.create_index('idx_generated_files_is_temporary', 'generated_files', ['is_temporary'])
    
    # Indexes for agent_history table
    op.create_index('idx_agent_history_agent_id', 'agent_history', ['agent_id'])
    op.create_index('idx_agent_history_action_type', 'agent_history', ['action_type'])
    op.create_index('idx_agent_history_created_at', 'agent_history', ['created_at'])
    op.create_index('idx_agent_history_author_id', 'agent_history', ['author_id'])
    
    # Indexes for templates table (if exists)
    try:
        op.create_index('idx_templates_name', 'templates', ['name'], unique=True)
        op.create_index('idx_templates_category', 'templates', ['category'])
        op.create_index('idx_templates_created_by', 'templates', ['created_by'])
        op.create_index('idx_templates_created_at', 'templates', ['created_at'])
        op.create_index('idx_templates_is_public', 'templates', ['is_public'])
    except Exception:
        # Table may not exist yet (will be created in future migrations)
        pass
    
    # Indexes for workflows table (if exists)
    try:
        op.create_index('idx_workflows_name', 'workflows', ['name'])
        op.create_index('idx_workflows_agent_id', 'workflows', ['agent_id'])
        op.create_index('idx_workflows_created_at', 'workflows', ['created_at'])
        op.create_index('idx_workflows_is_active', 'workflows', ['is_active'])
    except Exception:
        # Table may not exist yet (will be created in future migrations)
        pass


def downgrade():
    """Remove created indexes."""
    
    # Remove indexes in reverse order of creation
    
    # workflows table
    try:
        op.drop_index('idx_workflows_is_active', table_name='workflows')
        op.drop_index('idx_workflows_created_at', table_name='workflows')
        op.drop_index('idx_workflows_agent_id', table_name='workflows')
        op.drop_index('idx_workflows_name', table_name='workflows')
    except Exception:
        pass
    
    # templates table
    try:
        op.drop_index('idx_templates_is_public', table_name='templates')
        op.drop_index('idx_templates_created_at', table_name='templates')
        op.drop_index('idx_templates_created_by', table_name='templates')
        op.drop_index('idx_templates_category', table_name='templates')
        op.drop_index('idx_templates_name', table_name='templates')
    except Exception:
        pass
    
    # agent_history table
    op.drop_index('idx_agent_history_author_id', table_name='agent_history')
    op.drop_index('idx_agent_history_created_at', table_name='agent_history')
    op.drop_index('idx_agent_history_action_type', table_name='agent_history')
    op.drop_index('idx_agent_history_agent_id', table_name='agent_history')
    
    # generated_files table
    op.drop_index('idx_generated_files_is_temporary', table_name='generated_files')
    op.drop_index('idx_generated_files_file_format', table_name='generated_files')
    op.drop_index('idx_generated_files_created_at', table_name='generated_files')
    op.drop_index('idx_generated_files_execution_id', table_name='generated_files')
    op.drop_index('idx_generated_files_agent_id', table_name='generated_files')
    
    # executions table
    op.drop_index('idx_executions_completed_at', table_name='executions')
    op.drop_index('idx_executions_started_at', table_name='executions')
    op.drop_index('idx_executions_status_created_at', table_name='executions')
    op.drop_index('idx_executions_agent_id_created_at', table_name='executions')
    op.drop_index('idx_executions_model_used', table_name='executions')
    op.drop_index('idx_executions_workflow_id', table_name='executions')
    op.drop_index('idx_executions_executed_by', table_name='executions')
    op.drop_index('idx_executions_created_at', table_name='executions')
    op.drop_index('idx_executions_status', table_name='executions')
    op.drop_index('idx_executions_agent_id', table_name='executions')
    
    # agents table
    op.drop_index('idx_agents_is_active_created_at', table_name='agents')
    op.drop_index('idx_agents_model', table_name='agents')
    op.drop_index('idx_agents_project_id', table_name='agents')
    op.drop_index('idx_agents_created_by', table_name='agents')
    op.drop_index('idx_agents_created_at', table_name='agents')
    op.drop_index('idx_agents_is_active', table_name='agents')
    op.drop_index('idx_agents_name', table_name='agents')
