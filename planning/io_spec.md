# Node IO Specification Notes

## Goal

Remove hardcoded node input/output type definitions from `server/domain/rules/workflow_rules.py`.

Replace them with explicit node specification objects so that each node type has a single place that defines:

- input type
- output type
- required configuration keys

This should improve extensibility when adding new node types.

## Current Problem

Current code spreads node-type-specific rules across multiple places:

- `server/domain/rules/workflow_rules.py`
  - hardcodes node I/O types in `node_io_types`
- `server/domain/entities/node.py`
  - hardcodes required configuration keys per node type
- `server/services/processors/*`
  - contains the actual execution logic

As a result, adding a new node type requires editing multiple unrelated places, and the I/O contract is not represented as a first-class object.

## Target Design

Introduce explicit node specification types.

Example shape:

```python
class NodeIOType(str, Enum):
    PDF_FILE = "pdf_file"
    TEXT = "text"


class NodeSpec(BaseModel):
    node_type: NodeType
    input_type: NodeIOType
    output_type: NodeIOType
    required_config_keys: list[str]
```

Also introduce a registry for node specs.

Example:

```python
NODE_SPECS = {
    NodeType.EXTRACT_TEXT: NodeSpec(
        node_type=NodeType.EXTRACT_TEXT,
        input_type=NodeIOType.PDF_FILE,
        output_type=NodeIOType.TEXT,
        required_config_keys=[],
    ),
    NodeType.GENERATIVE_AI: NodeSpec(
        node_type=NodeType.GENERATIVE_AI,
        input_type=NodeIOType.TEXT,
        output_type=NodeIOType.TEXT,
        required_config_keys=["prompt"],
    ),
    NodeType.FORMATTER: NodeSpec(
        node_type=NodeType.FORMATTER,
        input_type=NodeIOType.TEXT,
        output_type=NodeIOType.TEXT,
        required_config_keys=["format_type"],
    ),
}
```

## Proposed File Changes

### 1. Add node spec definitions

Add:

- `server/domain/specs/node_spec.py`

This file should define:

- `NodeIOType`
- `NodeSpec`

### 2. Add node spec registry

Add:

- `server/domain/specs/node_spec_registry.py`

This file should:

- define the mapping from `NodeType` to `NodeSpec`
- expose a function or classmethod like `get_spec(node_type: NodeType) -> NodeSpec`
- raise a clear error for unsupported node types

### 3. Update `workflow_rules.py`

Update:

- `server/domain/rules/workflow_rules.py`

Change `_validate_io_compatibility(...)` so that it no longer defines `node_io_types` locally.

Instead it should:

- fetch `NodeSpec` for each node type
- compare `spec.output_type` and `next_spec.input_type`
- validate that the first node can accept the workflow input type

This file should remain responsible for workflow-level validation, but not for storing node-type-specific metadata.

### 4. Update `node.py`

Update:

- `server/domain/entities/node.py`

`Node` should continue to validate configuration values, but generic required key lookups should come from `NodeSpecRegistry`.

Specifically:

- `get_required_configuration_keys()` should delegate to `NodeSpecRegistry`
- hardcoded required key lists in helper methods should be reduced where practical

Deep validation can remain in `Node` for now.

Examples:

- `GENERATIVE_AI` still validates prompt is non-empty and model/temperature/max_tokens are valid
- `FORMATTER` still validates `replace` needs `find` and `replace_with`

In other words:

- `NodeSpec` owns static metadata
- `Node` owns richer value validation

### 5. Do not move execution logic

Do not change the execution flow architecture for this task.

`server/api/routers/executions.py` should still:

- iterate through ordered nodes
- get processor by node type from `ProcessorRegistry`
- call `processor.process(current_data, node.configuration)`

This task is only about moving node I/O contract metadata out of `WorkflowRules`.

## Design Rules

- `WorkflowRules` should validate workflow composition, not store hardcoded node-type metadata
- `NodeSpec` should represent static node-type metadata only
- `Node` should remain the runtime entity instance used inside a workflow
- `ProcessorRegistry` should remain the runtime lookup for executable behavior
- Adding a new node type should mainly require:
  - updating `NodeType`
  - adding a `NodeSpec`
  - adding a processor implementation
  - registering that processor

## Non-Goals

Do not implement:

- a full generic type system
- persistence for intermediate node input/output
- a refactor of execution orchestration
- queue/worker changes

## Acceptance Criteria

- `workflow_rules.py` no longer hardcodes `node_io_types`
- node I/O metadata is defined in a dedicated spec structure
- workflow validation reads node I/O information from the new spec registry
- `Node` can read required config keys from the node spec
- current supported nodes still behave the same:
  - `EXTRACT_TEXT: pdf_file -> text`
  - `GENERATIVE_AI: text -> text`
  - `FORMATTER: text -> text`
- adding a future node type does not require editing a hardcoded I/O dict inside `WorkflowRules`
