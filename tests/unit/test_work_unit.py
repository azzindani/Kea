"""
Tests for Work Unit and Work Board.
"""

import pytest
from datetime import datetime, timedelta


class TestWorkUnit:
    """Tests for WorkUnit model."""
    
    def test_create_work_unit(self):
        """Test work unit creation."""
        from services.orchestrator.core.work_unit import (
            WorkUnit, WorkType, Priority
        )
        
        work = WorkUnit.create(
            title="Analyze Tesla Revenue",
            work_type=WorkType.ANALYSIS,
            description="Deep dive into revenue streams",
            priority=Priority.HIGH,
        )
        
        assert work.work_id.startswith("work_")
        assert work.title == "Analyze Tesla Revenue"
        assert work.work_type == WorkType.ANALYSIS
        assert work.priority == Priority.HIGH
        
        print(f"\n✅ Created work: {work.work_id}")
    
    def test_work_lifecycle(self):
        """Test work status transitions."""
        from services.orchestrator.core.work_unit import (
            WorkUnit, WorkType, WorkStatus
        )
        
        work = WorkUnit.create("Test Task", WorkType.RESEARCH)
        
        # Initial state
        assert work.status == WorkStatus.PENDING
        
        # Assign
        work.assign("agent_123")
        assert work.status == WorkStatus.ASSIGNED
        assert work.assigned_to == "agent_123"
        
        # Start
        work.start()
        assert work.status == WorkStatus.IN_PROGRESS
        assert work.started_at is not None
        
        # Update progress
        work.update_progress(0.5)
        assert work.progress == 0.5
        
        # Complete
        work.complete(result={"revenue": "$81B"})
        assert work.status == WorkStatus.COMPLETED
        assert work.progress == 1.0
        assert work.result == {"revenue": "$81B"}
        assert work.completed_at is not None
        
        print("\n✅ Work lifecycle transitions work")
    
    def test_work_failure(self):
        """Test work failure handling."""
        from services.orchestrator.core.work_unit import WorkUnit, WorkType, WorkStatus
        
        work = WorkUnit.create("Failing Task", WorkType.EXECUTION)
        work.start()
        work.fail("Connection timeout")
        
        assert work.status == WorkStatus.FAILED
        assert work.error == "Connection timeout"
        
        print("\n✅ Work failure handling works")
    
    def test_work_blocking(self):
        """Test work blocking."""
        from services.orchestrator.core.work_unit import WorkUnit, WorkType, WorkStatus
        
        work = WorkUnit.create("Blocked Task", WorkType.ANALYSIS)
        work.block("work_dep_123")
        
        assert work.status == WorkStatus.BLOCKED
        assert work.blocked_by == "work_dep_123"
        
        print("\n✅ Work blocking works")
    
    def test_work_duration(self):
        """Test duration calculation."""
        from services.orchestrator.core.work_unit import WorkUnit, WorkType
        
        work = WorkUnit.create("Timed Task", WorkType.RESEARCH)
        work.start()
        work.complete()
        
        # Duration should be ~0 but not None
        assert work.duration is not None
        assert work.duration >= 0
        
        print(f"\n✅ Duration: {work.duration:.4f}s")


class TestWorkBoard:
    """Tests for WorkBoard."""
    
    def test_add_work(self):
        """Test adding work to board."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType
        )
        
        board = WorkBoard()
        work = WorkUnit.create("Task 1", WorkType.ANALYSIS)
        
        board.add(work)
        
        retrieved = board.get(work.work_id)
        assert retrieved is not None
        assert retrieved.title == "Task 1"
        
        print("\n✅ Work added to board")
    
    def test_get_by_status(self):
        """Test filtering by status."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, WorkStatus
        )
        
        board = WorkBoard()
        
        # Add 3 pending, 2 completed
        for i in range(3):
            board.add(WorkUnit.create(f"Pending {i}", WorkType.RESEARCH))
        
        for i in range(2):
            work = WorkUnit.create(f"Done {i}", WorkType.ANALYSIS)
            work.complete()
            board.add(work)
        
        pending = board.get_by_status(WorkStatus.PENDING)
        completed = board.get_by_status(WorkStatus.COMPLETED)
        
        assert len(pending) == 3
        assert len(completed) == 2
        
        print("\n✅ Status filtering works")
    
    def test_get_next_pending(self):
        """Test priority-based next work."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, Priority
        )
        
        board = WorkBoard()
        
        # Add low priority first
        low = WorkUnit.create("Low Priority", WorkType.RESEARCH, priority=Priority.LOW)
        board.add(low)
        
        # Add high priority second
        high = WorkUnit.create("High Priority", WorkType.RESEARCH, priority=Priority.HIGH)
        board.add(high)
        
        # Should get high priority first
        next_work = board.get_next_pending()
        assert next_work is not None
        assert next_work.priority == Priority.HIGH
        
        print("\n✅ Priority ordering works")
    
    def test_assign_work(self):
        """Test work assignment via board."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, WorkStatus
        )
        
        board = WorkBoard()
        work = WorkUnit.create("Assignable Task", WorkType.EXECUTION)
        board.add(work)
        
        success = board.assign(work.work_id, "agent_456", "dept_research")
        
        assert success is True
        assert work.assigned_to == "agent_456"
        assert work.status == WorkStatus.ASSIGNED
        
        print("\n✅ Board assignment works")
    
    def test_complete_work(self):
        """Test completing work via board."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, WorkStatus
        )
        
        board = WorkBoard()
        work = WorkUnit.create("Completable Task", WorkType.ANALYSIS)
        board.add(work)
        work.start()
        
        success = board.complete(work.work_id, result={"answer": 42})
        
        assert success is True
        assert work.status == WorkStatus.COMPLETED
        assert work.result == {"answer": 42}
        
        print("\n✅ Board completion works")
    
    def test_board_stats(self):
        """Test board statistics."""
        from services.orchestrator.core.work_unit import (
            WorkBoard, WorkUnit, WorkType, Priority
        )
        
        board = WorkBoard()
        
        board.add(WorkUnit.create("Task 1", WorkType.RESEARCH, priority=Priority.HIGH))
        board.add(WorkUnit.create("Task 2", WorkType.ANALYSIS, priority=Priority.NORMAL))
        board.add(WorkUnit.create("Task 3", WorkType.REVIEW, priority=Priority.LOW))
        
        stats = board.stats
        
        assert stats["total"] == 3
        assert stats["by_status"]["pending"] == 3
        assert stats["by_priority"]["HIGH"] == 1
        
        print(f"\n✅ Board stats: {stats}")
    
    def test_singleton(self):
        """Test work board singleton."""
        from services.orchestrator.core.work_unit import get_work_board
        
        board1 = get_work_board()
        board2 = get_work_board()
        
        assert board1 is board2
        
        print("\n✅ WorkBoard singleton works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
