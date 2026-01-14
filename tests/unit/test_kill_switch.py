"""
Tests for Kill Switch Emergency Controls.
"""

import pytest
import asyncio


class TestBlacklistEntry:
    """Tests for blacklist entries."""
    
    def test_create_entry(self):
        """Test blacklist entry creation."""
        from services.orchestrator.core.kill_switch import BlacklistEntry
        from datetime import datetime, timedelta
        
        entry = BlacklistEntry(
            name="failing_tool",
            reason="Repeated timeouts",
            until=datetime.utcnow() + timedelta(minutes=30),
        )
        
        assert entry.name == "failing_tool"
        assert entry.reason == "Repeated timeouts"
        assert entry.created_at is not None
        
        print("\n✅ BlacklistEntry created")


class TestKillSwitch:
    """Tests for KillSwitch."""
    
    def test_create_kill_switch(self):
        """Test kill switch creation."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        assert switch.is_emergency_stopped is False
        print("\n✅ KillSwitch created")
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self):
        """Test emergency stop."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        assert switch.is_emergency_stopped is False
        
        await switch.emergency_stop("Critical memory pressure")
        
        assert switch.is_emergency_stopped is True
        assert switch.can_proceed() is False
        
        print("\n✅ Emergency stop works")
    
    @pytest.mark.asyncio
    async def test_resume(self):
        """Test resume from emergency stop."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        await switch.emergency_stop("Test")
        assert switch.is_emergency_stopped is True
        
        await switch.resume()
        assert switch.is_emergency_stopped is False
        assert switch.can_proceed() is True
        
        print("\n✅ Resume works")
    
    @pytest.mark.asyncio
    async def test_emergency_callback(self):
        """Test emergency callback notification."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        callback_received = []
        
        async def on_emergency(reason):
            callback_received.append(reason)
        
        switch.on_emergency(on_emergency)
        
        await switch.emergency_stop("Test emergency")
        
        assert len(callback_received) == 1
        assert "Test emergency" in callback_received[0]
        
        print("\n✅ Emergency callback works")
    
    def test_blacklist_tool(self):
        """Test tool blacklisting."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        assert switch.is_tool_blacklisted("test_tool") is False
        
        switch.blacklist_tool("test_tool", reason="Failing", duration_minutes=5)
        
        assert switch.is_tool_blacklisted("test_tool") is True
        assert switch.can_proceed(tool_name="test_tool") is False
        
        print("\n✅ Tool blacklisting works")
    
    def test_unblacklist_tool(self):
        """Test removing tool from blacklist."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        switch.blacklist_tool("temp_tool", duration_minutes=10)
        assert switch.is_tool_blacklisted("temp_tool") is True
        
        switch.unblacklist_tool("temp_tool")
        assert switch.is_tool_blacklisted("temp_tool") is False
        
        print("\n✅ Unblacklist works")
    
    def test_pause_department(self):
        """Test department pausing."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        assert switch.is_department_paused("dept_research") is False
        
        switch.pause_department("dept_research")
        
        assert switch.is_department_paused("dept_research") is True
        assert switch.can_proceed(dept_id="dept_research") is False
        
        print("\n✅ Department pause works")
    
    def test_resume_department(self):
        """Test department resume."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        switch.pause_department("dept_finance")
        switch.resume_department("dept_finance")
        
        assert switch.is_department_paused("dept_finance") is False
        
        print("\n✅ Department resume works")
    
    def test_can_proceed_combined(self):
        """Test combined proceed checks."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # All clear
        assert switch.can_proceed(tool_name="tool_a", dept_id="dept_1") is True
        
        # Blacklist tool
        switch.blacklist_tool("tool_a", duration_minutes=5)
        assert switch.can_proceed(tool_name="tool_a", dept_id="dept_1") is False
        assert switch.can_proceed(tool_name="tool_b", dept_id="dept_1") is True
        
        print("\n✅ Combined proceed checks work")
    
    def test_singleton(self):
        """Test kill switch singleton."""
        from services.orchestrator.core.kill_switch import get_kill_switch
        
        ks1 = get_kill_switch()
        ks2 = get_kill_switch()
        
        assert ks1 is ks2
        
        print("\n✅ Singleton works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
