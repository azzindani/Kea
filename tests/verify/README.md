# Verify Tests

Standalone Python verification scripts that run without pytest.

## Quick Start

```bash
# Run full system health check
python tests/verify/verify_all.py

# Run v3.0 enterprise kernel verification
python tests/verify/verify_enterprise_kernel.py

# Run v2.x features verification  
python tests/verify/verify_v2_features.py

# Run MCP servers simulation
python tests/simulation/run_simulation.py
```

## No Dependencies Required

These scripts only need:
- Python 3.10+
- The Project codebase

No pytest, no test frameworks - just `python script.py`.

## Output

Each script prints:
- ✅ for passing checks
- ❌ for failing checks
- Summary with pass/fail counts
- Exit code 0 (success) or 1 (failure)

## Example Output

```
=======================================================
🚀 KEA SYSTEM HEALTH CHECK
=======================================================

──────────────────────────────────────
  CORE IMPORTS
──────────────────────────────────────
  ✅ organization
  ✅ work_unit
  ✅ messaging
  ✅ supervisor

📊 HEALTH CHECK SUMMARY
=======================================================
  Core Imports: ✅ HEALTHY
  MCP Servers: ✅ HEALTHY
  Functional Tests: ✅ HEALTHY

  Result: 3/3 categories healthy

  🎉 ALL SYSTEMS OPERATIONAL!
```
