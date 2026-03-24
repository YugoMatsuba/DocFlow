import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.workflow import Workflow
from domain.entities.node import Node
from domain.entities.execution import Execution, ExecutionStatus
from domain.enums.node_type import NodeType
from services.execution_dispatcher import ExecutionDispatcher

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_execution_repository():
    """Mock execution repository for unit tests."""
    return AsyncMock()

@pytest.fixture
def mock_workflow_repository():
    """Mock workflow repository for unit tests."""
    return AsyncMock()

@pytest.fixture
def mock_execution_dispatcher():
    """Mock execution dispatcher for unit tests."""
    return MagicMock(spec=ExecutionDispatcher)

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for unit tests."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock()
    return mock_client

@pytest.fixture
def sample_workflow():
    """Create a sample workflow for testing."""
    workflow = Workflow.create(
        name="Test Workflow",
        description="A test workflow"
    )

    # Add extract text node
    extract_node = Node.create(
        name="Extract Text",
        node_type=NodeType.EXTRACT_TEXT,
        configuration={},
        workflow_id=workflow.id,
        order=0
    )
    workflow.nodes.append(extract_node)

    # Add formatter node
    formatter_node = Node.create(
        name="Format Text",
        node_type=NodeType.FORMATTER,
        configuration={"format_type": "uppercase"},
        workflow_id=workflow.id,
        order=1
    )
    workflow.nodes.append(formatter_node)

    return workflow

@pytest.fixture
def sample_node():
    """Create a sample node for testing."""
    return Node.create(
        name="Test Node",
        node_type=NodeType.FORMATTER,
        configuration={"format_type": "uppercase"},
        workflow_id="test-workflow-id",
        order=0
    )

@pytest.fixture
def sample_execution():
    """Create a sample execution for testing."""
    return Execution.create(
        workflow_id="test-workflow-id",
        input_file_path="test.pdf"
    )

@pytest.fixture
def temp_upload_dir():
    """Create temporary directory for file uploads in tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_pdf_bytes():
    """Create a minimal PDF file content for testing."""
    # This is a minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000010 00000 n
0000000053 00000 n
0000000104 00000 n
0000000179 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
272
%%EOF"""
    return pdf_content

# Removed client fixture to avoid importing main app for unit tests

# Mock environment variables for tests
@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock environment variables for all tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("UPLOAD_DIR", "/tmp/test_uploads")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")  # Reduce test output