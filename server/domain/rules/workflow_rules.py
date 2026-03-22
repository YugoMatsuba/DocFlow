from typing import List
from domain.entities.workflow import Workflow
from domain.entities.node import Node
from domain.enums.node_type import NodeType
from domain.specs.node_spec_registry import NodeSpecRegistry
from domain.specs.node_spec import NodeIOType

class WorkflowRules:
    """Domain rules for workflow validation and constraints"""

    @staticmethod
    def validate_workflow(workflow: Workflow) -> List[str]:
        """Validate workflow and return list of errors"""
        errors = []

        if not workflow.nodes:
            errors.append("Workflow must have at least one node")
            return errors

        # Sort nodes by order to check sequence
        sorted_nodes = sorted(workflow.nodes, key=lambda x: x.order)

        # Check node order constraints
        errors.extend(WorkflowRules._validate_node_order(sorted_nodes))

        # Check input/output compatibility
        errors.extend(WorkflowRules._validate_io_compatibility(sorted_nodes))

        return errors

    @staticmethod
    def _validate_node_order(nodes: List[Node]) -> List[str]:
        """Validate node ordering"""
        errors = []

        # Check for duplicate orders
        orders = [node.order for node in nodes]
        if len(orders) != len(set(orders)):
            errors.append("Nodes cannot have duplicate order values")

        return errors

    @staticmethod
    def _validate_io_compatibility(nodes: List[Node]) -> List[str]:
        """Validate input/output compatibility between nodes"""
        errors = []

        if not nodes:
            return errors

        try:
            # Check if first node can handle file input (for PDF workflows)
            first_node = nodes[0]
            first_spec = NodeSpecRegistry.get_spec(first_node.node_type)

            if first_spec.input_type != NodeIOType.PDF_FILE:
                errors.append(f"First node must be able to handle PDF input. Found {first_node.node_type} which expects {first_spec.input_type.value}")

            # Check compatibility between consecutive nodes
            for i in range(len(nodes) - 1):
                current_node = nodes[i]
                next_node = nodes[i + 1]

                current_spec = NodeSpecRegistry.get_spec(current_node.node_type)
                next_spec = NodeSpecRegistry.get_spec(next_node.node_type)

                if current_spec.output_type != next_spec.input_type:
                    errors.append(
                        f"Node '{current_node.name}' output type '{current_spec.output_type.value}' "
                        f"is incompatible with node '{next_node.name}' input type '{next_spec.input_type.value}'"
                    )

        except ValueError as e:
            errors.append(f"Unknown node type found during validation: {str(e)}")

        return errors

    @staticmethod
    def validate_execution_input(workflow: Workflow, input_type: str) -> List[str]:
        """Validate that execution input is compatible with workflow"""
        errors = []

        if not workflow.nodes:
            errors.append("Cannot execute workflow with no nodes")
            return errors

        first_node = sorted(workflow.nodes, key=lambda x: x.order)[0]

        try:
            first_spec = NodeSpecRegistry.get_spec(first_node.node_type)

            # For MVP, we only support PDF input
            if input_type == "pdf_file" and first_spec.input_type != NodeIOType.PDF_FILE:
                errors.append(f"PDF input requires first node to accept PDF files, found {first_node.node_type} which expects {first_spec.input_type.value}")

        except ValueError as e:
            errors.append(f"Unknown node type found: {str(e)}")

        return errors
