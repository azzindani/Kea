"""
Unit tests for services/orchestrator/core/assembler.py

Tests the Node Assembly Engine: ArtifactStore, resolve_inputs, and NodeAssembler.
"""

import pytest
from unittest.mock import MagicMock, patch

from services.orchestrator.core.assembler import (
    ArtifactStore,
    NodeAssembler,
    resolve_inputs,
    create_assembler,
    PLACEHOLDER_PATTERN,
)


# ============================================================================
# ArtifactStore Tests
# ============================================================================

class TestArtifactStore:
    """Tests for ArtifactStore class."""
    
    def test_store_and_get(self):
        """Test basic store and retrieval."""
        store = ArtifactStore()
        store.store("step1", "output_csv", "/vault/data.csv")
        
        result = store.get("step1.artifacts.output_csv")
        assert result == "/vault/data.csv"
        
    def test_get_without_artifacts_keyword(self):
        """Test retrieval with short reference format."""
        store = ArtifactStore()
        store.store("fetch", "prices", "/vault/prices.csv")
        
        # Both formats should work
        assert store.get("fetch.artifacts.prices") == "/vault/prices.csv"
        assert store.get("fetch.prices") == "/vault/prices.csv"
        
    def test_get_missing_artifact(self):
        """Test retrieval of non-existent artifact returns None."""
        store = ArtifactStore()
        assert store.get("nonexistent.artifacts.key") is None
        
    def test_list_artifacts(self):
        """Test listing all artifacts."""
        store = ArtifactStore()
        store.store("s1", "a", "value_a")
        store.store("s1", "b", "value_b")
        store.store("s2", "c", "value_c")
        
        all_artifacts = store.list_artifacts()
        assert "s1" in all_artifacts
        assert "s2" in all_artifacts
        assert all_artifacts["s1"]["a"] == "value_a"
        
    def test_list_artifacts_for_step(self):
        """Test listing artifacts for a specific step."""
        store = ArtifactStore()
        store.store("s1", "a", "value_a")
        store.store("s2", "b", "value_b")
        
        step_artifacts = store.list_artifacts("s1")
        assert "s1" in step_artifacts
        assert "s2" not in step_artifacts
        
    def test_has_artifact(self):
        """Test artifact existence check."""
        store = ArtifactStore()
        store.store("step1", "key", "value")
        
        assert store.has_artifact("step1", "key") is True
        assert store.has_artifact("step1", "other") is False
        assert store.has_artifact("step2", "key") is False
        
    def test_store_with_context_pool(self):
        """Test that store also writes to TaskContextPool if provided."""
        mock_pool = MagicMock()
        store = ArtifactStore(context_pool=mock_pool)
        
        store.store("step1", "output", "data")
        
        mock_pool.store_data.assert_called_once()
        # Verify the key contains the expected pattern
        call_args = mock_pool.store_data.call_args
        args, kwargs = call_args
        assert "step1.artifacts.output" in args[0]


# ============================================================================
# resolve_inputs Tests
# ============================================================================

class TestResolveInputs:
    """Tests for resolve_inputs function."""
    
    def test_single_placeholder(self):
        """Test resolving a single placeholder."""
        store = ArtifactStore()
        store.store("fetch_data", "prices_csv", "/vault/bbca.csv")
        
        input_mapping = {"csv_path": "{{fetch_data.artifacts.prices_csv}}"}
        resolved = resolve_inputs(input_mapping, store)
        
        assert resolved["csv_path"] == "/vault/bbca.csv"
        
    def test_multiple_placeholders(self):
        """Test resolving multiple placeholders in different keys."""
        store = ArtifactStore()
        store.store("s1", "a", "value_a")
        store.store("s2", "b", "value_b")
        
        input_mapping = {
            "input1": "{{s1.artifacts.a}}",
            "input2": "{{s2.artifacts.b}}"
        }
        resolved = resolve_inputs(input_mapping, store)
        
        assert resolved["input1"] == "value_a"
        assert resolved["input2"] == "value_b"
        
    def test_placeholder_in_string(self):
        """Test placeholder embedded in a larger string."""
        store = ArtifactStore()
        store.store("fetch", "path", "/data/file.csv")
        
        input_mapping = {"command": "process --file={{fetch.artifacts.path}} --verbose"}
        resolved = resolve_inputs(input_mapping, store)
        
        assert resolved["command"] == "process --file=/data/file.csv --verbose"
        
    def test_missing_artifact(self):
        """Test that missing artifacts are not replaced."""
        store = ArtifactStore()
        
        input_mapping = {"path": "{{nonexistent.artifacts.key}}"}
        resolved = resolve_inputs(input_mapping, store)
        
        # Placeholder should remain unchanged
        assert "{{" in resolved["path"]
        
    def test_no_placeholders(self):
        """Test input with no placeholders passes through."""
        store = ArtifactStore()
        
        input_mapping = {"static": "just a string", "number": 42}
        resolved = resolve_inputs(input_mapping, store)
        
        assert resolved["static"] == "just a string"
        assert resolved["number"] == 42
        
    def test_empty_input_mapping(self):
        """Test empty input mapping returns empty dict."""
        store = ArtifactStore()
        resolved = resolve_inputs({}, store)
        assert resolved == {}


# ============================================================================
# NodeAssembler Tests
# ============================================================================

class TestNodeAssembler:
    """Tests for NodeAssembler class."""
    
    def test_topological_sort_numeric_phases(self):
        """Test sorting tasks by numeric phase."""
        store = ArtifactStore()
        assembler = NodeAssembler(store)
        
        # Create mock tasks with phase attribute
        tasks = [
            type('Task', (), {'phase': '2', 'task_id': 't2'})(),
            type('Task', (), {'phase': '1', 'task_id': 't1'})(),
            type('Task', (), {'phase': '3', 'task_id': 't3'})(),
        ]
        
        phases = assembler.topological_sort(tasks)
        
        assert len(phases) == 3
        assert phases[0].phase == 1  # Phase 1 first
        assert phases[1].phase == 2
        assert phases[2].phase == 3
        
    def test_topological_sort_parallel_in_phase(self):
        """Test that tasks in same phase are grouped together."""
        store = ArtifactStore()
        assembler = NodeAssembler(store)
        
        tasks = [
            type('Task', (), {'phase': '1', 'task_id': 't1a'})(),
            type('Task', (), {'phase': '1', 'task_id': 't1b'})(),
            type('Task', (), {'phase': '2', 'task_id': 't2'})(),
        ]
        
        phases = assembler.topological_sort(tasks)
        
        assert len(phases) == 2
        assert len(phases[0].tasks) == 2  # Two tasks in phase 1
        assert len(phases[1].tasks) == 1  # One task in phase 2
        
    def test_resolve_task_inputs(self):
        """Test resolving inputs for a task."""
        store = ArtifactStore()
        store.store("prev", "output", "resolved_value")
        assembler = NodeAssembler(store)
        
        task = type('Task', (), {
            'task_id': 'current',
            'input_mapping': {'input': '{{prev.artifacts.output}}'}
        })()
        
        resolved = assembler.resolve_task_inputs(task)
        assert resolved["input"] == "resolved_value"
        
    def test_store_task_artifacts_from_string(self):
        """Test storing artifacts from string result."""
        store = ArtifactStore()
        assembler = NodeAssembler(store)
        
        task = type('Task', (), {
            'task_id': 'step1',
            'output_artifact': 'result'
        })()
        
        assembler.store_task_artifacts(task, "the result value")
        
        assert store.get("step1.artifacts.result") == "the result value"
        
    def test_store_task_artifacts_from_dict(self):
        """Test storing artifacts from dict result."""
        store = ArtifactStore()
        assembler = NodeAssembler(store)
        
        task = type('Task', (), {
            'task_id': 'step1',
            'output_artifact': 'data'
        })()
        
        assembler.store_task_artifacts(task, {"key": "value"})
        
        stored = store.get("step1.artifacts.data")
        assert stored == {"key": "value"}


# ============================================================================
# Integration Tests
# ============================================================================

class TestAssemblerIntegration:
    """Integration tests for the full pipeline."""
    
    def test_two_step_pipeline(self):
        """Test a simple two-step pipeline with data passing."""
        # Step 1: Creates an artifact
        # Step 2: Consumes the artifact via input_mapping
        
        store = ArtifactStore()
        assembler = NodeAssembler(store)
        
        # Simulate step 1 execution
        task1 = type('Task', (), {
            'task_id': 'fetch',
            'output_artifact': 'data_path',
            'phase': '1'
        })()
        
        assembler.store_task_artifacts(task1, "/vault/data.csv")
        
        # Simulate step 2 input resolution
        task2 = type('Task', (), {
            'task_id': 'process',
            'input_mapping': {'file': '{{fetch.artifacts.data_path}}'},
            'phase': '2'
        })()
        
        resolved = assembler.resolve_task_inputs(task2)
        
        assert resolved["file"] == "/vault/data.csv"
        
    def test_create_assembler_helper(self):
        """Test the create_assembler convenience function."""
        assembler = create_assembler()
        
        assert assembler is not None
        assert assembler.store is not None


# ============================================================================
# Placeholder Pattern Tests
# ============================================================================

class TestPlaceholderPattern:
    """Tests for the placeholder regex pattern."""
    
    def test_matches_standard_format(self):
        """Test matching standard {{step.artifacts.key}} format."""
        matches = PLACEHOLDER_PATTERN.findall("{{step1.artifacts.output}}")
        assert matches == ["step1.artifacts.output"]
        
    def test_matches_multiple(self):
        """Test matching multiple placeholders."""
        text = "{{a.artifacts.x}} and {{b.artifacts.y}}"
        matches = PLACEHOLDER_PATTERN.findall(text)
        assert len(matches) == 2
        assert "a.artifacts.x" in matches
        assert "b.artifacts.y" in matches
        
    def test_no_match_for_static_text(self):
        """Test that static text doesn't match."""
        matches = PLACEHOLDER_PATTERN.findall("just plain text")
        assert matches == []
