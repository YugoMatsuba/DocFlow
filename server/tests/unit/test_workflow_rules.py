import pytest
from domain.entities.workflow import Workflow
from domain.entities.node import Node
from domain.enums.node_type import NodeType
from domain.rules.workflow_rules import WorkflowRules


class TestWorkflowRules:
    """Test cases for WorkflowRules validation logic"""

    def test_validate_workflow_with_no_nodes(self):
        """Test validation when workflow has no nodes"""
        workflow = Workflow.create("Empty Workflow")

        errors = WorkflowRules.validate_workflow(workflow)

        assert len(errors) == 1
        assert "Workflow must have at least one node" in errors[0]

    def test_validate_workflow_with_first_node_not_accepting_pdf(self):
        """Test validation when first node cannot handle PDF input"""
        workflow = Workflow.create("Test Workflow")

        # Add a FORMATTER node as first node (which expects TEXT, not PDF_FILE)
        formatter_node = Node.create(
            name="First Formatter",
            node_type=NodeType.FORMATTER,
            configuration={"format_type": "uppercase"},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(formatter_node)

        errors = WorkflowRules.validate_workflow(workflow)

        assert len(errors) >= 1
        assert any("First node must be able to handle PDF input" in error for error in errors)

    def test_validate_workflow_with_incompatible_node_io(self):
        """Test validation when consecutive nodes have incompatible input/output types"""
        workflow = Workflow.create("Test Workflow")

        # Add EXTRACT_TEXT node (output: TEXT)
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(extract_node)

        # Add another EXTRACT_TEXT node (input: PDF_FILE) - should be incompatible
        extract_node2 = Node.create(
            name="Extract2",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=1
        )
        workflow.nodes.append(extract_node2)

        errors = WorkflowRules.validate_workflow(workflow)

        assert len(errors) >= 1
        assert any("output type" in error and "incompatible" in error for error in errors)

    def test_validate_workflow_with_duplicate_orders(self):
        """Test validation when nodes have duplicate order values"""
        workflow = Workflow.create("Test Workflow")

        # Add two nodes with same order
        node1 = Node.create(
            name="Node1",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        node2 = Node.create(
            name="Node2",
            node_type=NodeType.FORMATTER,
            configuration={"format_type": "uppercase"},
            workflow_id=workflow.id,
            order=0  # Duplicate order
        )
        workflow.nodes.extend([node1, node2])

        errors = WorkflowRules.validate_workflow(workflow)

        assert len(errors) >= 1
        assert any("duplicate order" in error for error in errors)

    def test_validate_workflow_valid_workflow(self):
        """Test validation of a properly constructed workflow"""
        workflow = Workflow.create("Valid Workflow")

        # Add EXTRACT_TEXT -> FORMATTER sequence
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )

        formatter_node = Node.create(
            name="Format",
            node_type=NodeType.FORMATTER,
            configuration={"format_type": "uppercase"},
            workflow_id=workflow.id,
            order=1
        )

        workflow.nodes.extend([extract_node, formatter_node])

        errors = WorkflowRules.validate_workflow(workflow)

        assert len(errors) == 0

    def test_validate_workflow_complex_valid_chain(self):
        """Test validation of a complex but valid workflow chain"""
        workflow = Workflow.create("Complex Workflow")

        # EXTRACT_TEXT -> GENERATIVE_AI -> FORMATTER
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )

        ai_node = Node.create(
            name="AI Process",
            node_type=NodeType.GENERATIVE_AI,
            configuration={"prompt": "Summarize the text"},
            workflow_id=workflow.id,
            order=1
        )

        formatter_node = Node.create(
            name="Format",
            node_type=NodeType.FORMATTER,
            configuration={"format_type": "lowercase"},
            workflow_id=workflow.id,
            order=2
        )

        workflow.nodes.extend([extract_node, ai_node, formatter_node])

        errors = WorkflowRules.validate_workflow(workflow)

        assert len(errors) == 0

    def test_validate_execution_input_no_nodes(self):
        """Test execution input validation when workflow has no nodes"""
        workflow = Workflow.create("Empty Workflow")

        errors = WorkflowRules.validate_execution_input(workflow, "pdf_file")

        assert len(errors) == 1
        assert "Cannot execute workflow with no nodes" in errors[0]

    def test_validate_execution_input_pdf_with_incompatible_first_node(self):
        """Test PDF input validation when first node doesn't accept PDF"""
        workflow = Workflow.create("Test Workflow")

        formatter_node = Node.create(
            name="Format",
            node_type=NodeType.FORMATTER,
            configuration={"format_type": "uppercase"},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(formatter_node)

        errors = WorkflowRules.validate_execution_input(workflow, "pdf_file")

        assert len(errors) == 1
        assert "PDF input requires first node to accept PDF files" in errors[0]

    def test_validate_execution_input_pdf_with_compatible_first_node(self):
        """Test PDF input validation when first node accepts PDF"""
        workflow = Workflow.create("Test Workflow")

        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(extract_node)

        errors = WorkflowRules.validate_execution_input(workflow, "pdf_file")

        assert len(errors) == 0

    def test_validate_workflow_with_unknown_node_type(self, monkeypatch):
        """Test validation behavior when an unknown node type is encountered"""
        workflow = Workflow.create("Test Workflow")

        # Create a node with a valid type first
        node = Node.create(
            name="Test",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )

        # Mock the node_type to be an unknown type
        monkeypatch.setattr(node, 'node_type', 'UNKNOWN_TYPE')
        workflow.nodes.append(node)

        errors = WorkflowRules.validate_workflow(workflow)

        assert len(errors) >= 1
        assert any("Unknown node type found" in error for error in errors)