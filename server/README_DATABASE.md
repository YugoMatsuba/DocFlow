# Database Setup Guide

This guide explains how to set up PostgreSQL and run database migrations for the LayerX Workflow System.

## Prerequisites

1. **PostgreSQL Installation** (Local)
   ```bash
   # macOS with Homebrew
   brew install postgresql@15
   brew services start postgresql@15

   # Ubuntu/Debian
   sudo apt-get install postgresql-15 postgresql-contrib-15

   # Windows
   # Download and install from: https://www.postgresql.org/download/windows/
   ```

2. **Python Dependencies**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

## Database Setup

### 1. Create Database and User

Connect to PostgreSQL as superuser and create the database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE layerx_workflow_db;

# Create user (optional - you can use default 'postgres' user)
CREATE USER yugo WITH PASSWORD 'layerx_assignment';
GRANT ALL PRIVILEGES ON DATABASE layerx_workflow_db TO yugo;

# Exit psql
\q
```

### 2. Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Update database connection settings in `.env`:

```env
# Database Configuration (Local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/layerx_workflow_db
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/layerx_workflow_db
```

### 3. Run Database Migrations

Execute the Alembic migration to create tables:

```bash
# Navigate to server directory
cd server

# Run the migration
alembic upgrade head
```

This will create the following tables:
- `workflows` - Stores workflow definitions
- `nodes` - Stores node configurations within workflows
- `workflow_executions` - Stores execution history and results

### 4. Verify Database Setup

You can verify the tables were created successfully:

```bash
# Connect to the database
psql -U postgres -d layerx_workflow_db

# List tables
\dt

# Check table structure
\d workflows
\d nodes
\d workflow_executions

# Exit
\q
```

## Database Schema

### Tables Overview

#### workflows
- **id**: Primary key (string/UUID)
- **name**: Workflow name (required)
- **description**: Optional description
- **created_at**, **updated_at**: Timestamps
- **is_active**: Soft delete flag

#### nodes
- **id**: Primary key (string/UUID)
- **workflow_id**: Foreign key to workflows
- **node_type**: Type of node ('extract_text', 'generative_ai', 'formatter')
- **config**: JSON configuration for the node
- **order_index**: Order within workflow
- **created_at**: Timestamp

#### workflow_executions
- **id**: Primary key (string/UUID)
- **workflow_id**: Foreign key to workflows
- **input_text**: Text input for processing
- **output_text**: Final processed output
- **status**: Execution status ('pending', 'running', 'completed', 'failed', 'cancelled')
- **started_at**, **completed_at**: Execution timestamps
- **error_message**: Error details if failed
- **execution_context**: JSON metadata

### Indexes

The schema includes performance indexes on:
- `workflows.created_at`
- `nodes.workflow_id, order_index`
- `workflow_executions.workflow_id, status`
- `workflow_executions.status, started_at`

### Constraints

- **Foreign Keys**: Proper relationships with CASCADE delete
- **Unique Constraints**: `workflow_id + order_index` in nodes table
- **Check Constraints**: Valid enum values for node_type and execution status

## Migration Commands

```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade to previous version
alembic downgrade -1

# Generate new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"
```

## Troubleshooting

### Connection Issues

1. **PostgreSQL not running**:
   ```bash
   # Check if PostgreSQL is running
   pg_isready -U postgres

   # Start PostgreSQL (macOS with Homebrew)
   brew services start postgresql@15
   ```

2. **Database doesn't exist**:
   ```bash
   createdb -U postgres layerx_workflow_db
   ```

3. **Permission denied**:
   ```bash
   # Reset PostgreSQL user password
   psql -U postgres
   ALTER USER postgres PASSWORD 'postgres';
   ```

### Migration Issues

1. **Import errors in migration**:
   - Ensure all model imports are correct in `alembic/env.py`
   - Check that the server directory is in Python path

2. **Migration conflicts**:
   ```bash
   # Reset to specific revision
   alembic downgrade <revision_id>

   # Or start fresh (WARNING: destroys data)
   alembic downgrade base
   alembic upgrade head
   ```

## Development Workflow

1. **Making model changes**:
   - Update SQLAlchemy models in `infrastructure/db/models/`
   - Generate migration: `alembic revision --autogenerate -m "description"`
   - Review and edit the generated migration file
   - Apply migration: `alembic upgrade head`

2. **Database reset** (development only):
   ```bash
   # Drop all tables
   alembic downgrade base

   # Recreate all tables
   alembic upgrade head
   ```

This completes the database setup for the LayerX Workflow System!