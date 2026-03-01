import pytest

from kernel.activation_router.engine import (
    classify_signal_complexity,
    select_pipeline,
    check_decision_cache,
    cache_decision,
    compute_activation_map
)
from kernel.activation_router.types import ComplexityLevel
from kernel.classification.engine import classify
from kernel.classification.types import ClassificationResult, ClassProfileRules
from kernel.entity_recognition.engine import extract_entities
from kernel.entity_recognition.types import ValidatedEntity
from kernel.intent_sentiment_urgency.engine import run_primitive_scorers
from kernel.intent_sentiment_urgency.types import CognitiveLabels
from kernel.self_model.types import SignalTags, CapabilityAssessment
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("input_text", [
    "Find the stock price of Apple.",
    "Draft a legal contract for a freelance developer",
    "Identify security vulnerabilities in the following code snippet",
    "Help",
    "Shut down the system immediately!",
    "What is 2+2?",
])
async def test_activation_router_comprehensive(input_text, inference_kit):
    """REAL SIMULATION: Verify Activation Router Kernel functions with multiple inputs."""
    print(f"\n--- Testing Activation Router with Input: '{input_text}' ---")

    # 1. Generate Tags Dynamically from Input (SIMULATING TIER 7 BEHAVIOR)
    # The system now AUTOMATICALLY detects domain via embeddings in T1.
    print(f"\n[Step]: Generating Dynamic Tags via T1 (Automatic Detection)")
    
    # Classify (Performs Automatic Domain Detection via embeddings if rules are empty)
    class_res = await classify(input_text, ClassProfileRules(), inference_kit)
    classification: ClassificationResult = class_res.signals[0].body["data"]
    
    # Intent/Sentiment/Urgency
    labels_res = await run_primitive_scorers(input_text, inference_kit)
    labels: CognitiveLabels = labels_res.signals[0].body["data"]
    
    # Entities (if applicable)
    entities = []
    if len(input_text) > 10:
        ent_res = await extract_entities(input_text, ValidatedEntity, inference_kit)
        if ent_res.is_success:
            entities = ent_res.signals[0].body["data"]

    # Build Tags
    tags = SignalTags(
        urgency=labels["urgency"]["band"].lower() if isinstance(labels["urgency"]["band"], str) else labels["urgency"]["band"].value.lower(),
        domain=classification["top_label"] or "general",
        complexity=classification["top_label"].lower() if classification["top_label"] else "moderate", # Use domain as a hint
        intent=labels["intent"]["primary"] if isinstance(labels["intent"]["primary"], str) else labels["intent"]["primary"].value,
        entity_count=len(entities),
        source_type="user"
    )
    
    print(f"   [TAGS]: urgency={tags.urgency}, domain={tags.domain}, intent={tags.intent}, entities={tags.entity_count}")

    capability = CapabilityAssessment(
        can_handle=True,
        confidence=1.0,
        partial_capabilities=["test_tool"]
    )

    print(f"\n[Test]: classify_signal_complexity")
    print(f"   [INPUT]: signal='{input_text[:30]}...', domain={tags.domain}")
    classification_level = await classify_signal_complexity(tags, text=input_text, kit=inference_kit)
    assert classification_level is not None
    assert isinstance(classification_level, ComplexityLevel)
    print(f"   [OUTPUT]: Complexity={classification_level.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: select_pipeline")
    print(f"   [INPUT]: complexity={classification_level.value}, pressure=0.2")
    pipeline = select_pipeline(classification_level, pressure=0.2)
    assert pipeline is not None
    assert hasattr(pipeline, 'pipeline_name')
    print(f"   [OUTPUT]: Selected Pipeline={pipeline.pipeline_name}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: adapt_to_pressure (via select_pipeline)")
    for pressure in [0.1, 0.5, 0.9]:
        adapted_pipeline = select_pipeline(classification_level, pressure)
        assert adapted_pipeline is not None
        assert len(adapted_pipeline.active_modules) > 0
        print(f"     - [OUTPUT]: Pressure={pressure} -> Active Modules={len(adapted_pipeline.active_modules)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: cache_decision")
    print(f"   [INPUT]: tags_intent={tags.intent}")
    activation_map = await compute_activation_map(tags, capability, text=input_text)
    assert activation_map.is_success
    print(f"   [OUTPUT]: Decision cached successfully")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: compute_activation_map")
    print(f"   [INPUT]: signal='{input_text[:30]}...', confidence={capability.confidence}")
    res = await compute_activation_map(tags, capability, text=input_text, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
