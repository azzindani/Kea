
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.config import get_settings
from services.orchestrator.core.prompt_factory import PromptFactory
from services.orchestrator.core.prompt_factory import load_prompts_config

def verify_system():
    print("🔍 Starting System Verification...")
    
    # 1. Verify Config Loading
    try:
        settings = get_settings()
        print(f"✅ Config Loaded")
        
        # Check defaults
        model = settings.models.default_model
        print(f"   - Model: {model}")
        
        timeout = settings.timeouts.llm_completion
        print(f"   - Completion Timeout: {timeout}")
        
        max_cpu = settings.governance.max_cpu_percent
        print(f"   - Max CPU: {max_cpu}%")
        
        if model == "nvidia/nemotron-3-nano-30b-a3b:free" and max_cpu == 90.0:
            print("   ✅ Values match settings.yaml")
        else:
            print(f"   ⚠️ Values do NOT match expected defaults (Model={model}, CPU={max_cpu})")
            
    except Exception as e:
        print(f"❌ Config Verification Failed: {e}")
        return

    # 2. Verify Prompt Loading
    try:
        print("\n🔍 Verifying Prompt Factory...")
        factory = PromptFactory()
        
        # Check if domains loaded
        domain_count = len(factory._domain_templates)
        print(f"   - Loaded {domain_count} domain templates")
        
        # Check if tasks loaded
        task_count = len(factory._task_modifiers)
        print(f"   - Loaded {task_count} task modifiers")
        
        if domain_count > 0 and task_count > 0:
             print("   ✅ Prompt Factory initialized correctly")
        else:
             print("   ❌ Prompt Factory empty!")
             
    except Exception as e:
        print(f"❌ Prompt Verification Failed: {e}")

    print("\n🏁 Verification Complete")

if __name__ == "__main__":
    verify_system()
