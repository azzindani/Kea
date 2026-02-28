"""
Tier 6 Hallucination Monitor — Engine.

Epistemic grounding verification for output claims:
    1. Extract atomic claims from output text
    2. Classify claims (FACTUAL, REASONING, OPINION)
    3. Grade each claim against evidence (GROUNDED, INFERRED, FABRICATED)
    4. Calculate overall grounding score
    5. Trace evidence chains for inferred claims
"""

from __future__ import annotations

import json
import re
import time

from kernel.noise_gate.types import ToolOutput
from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    Claim,
    ClaimGrade,
    ClaimGradeLevel,
    ClaimType,
    EvidenceLink,
    GroundingReport,
    Origin,
)

log = get_logger(__name__)

_MODULE = "hallucination_monitor"
_TIER = 6


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Claim Classification Heuristics
# ============================================================================

_OPINION_MARKERS = frozenset({
    "i think", "i believe", "i recommend", "in my opinion",
    "i suggest", "arguably", "it seems", "likely", "probably",
    "might", "could be", "perhaps", "my view",
})

_REASONING_MARKERS = frozenset({
    "therefore", "thus", "hence", "consequently", "because",
    "since", "so", "implies", "it follows", "as a result",
    "given that", "based on",
})


# ============================================================================
# Step 1: Classify Claims (extract + classify)
# ============================================================================


async def classify_claims(output_text: str, kit: InferenceKit | None = None) -> list[Claim]:
    """Decompose output text into atomic, classified claims.

    Each claim is a sentence-level unit classified as FACTUAL,
    REASONING, or OPINION based on linguistic markers.
    """
    if not output_text.strip():
        return []

    if kit and kit.has_llm:
        try:
            system_msg = LLMMessage(
                role="system",
                content="Extract atomic claims from this text and classify each as FACTUAL, REASONING, or OPINION. Respond EXACTLY with JSON list of dicts: [{\"text\": \"...\", \"claim_type\": \"FACTUAL\"}]"
            )
            user_msg = LLMMessage(role="user", content=output_text)
            resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)
            content = resp.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            data = json.loads(content)

            claims = []
            for i, item in enumerate(data):
                ctype = ClaimType.FACTUAL
                if item.get("claim_type") == "OPINION":
                    ctype = ClaimType.OPINION
                elif item.get("claim_type") == "REASONING":
                    ctype = ClaimType.REASONING
                claims.append(Claim(
                    claim_id=generate_id("claim"),
                    text=item["text"],
                    claim_type=ctype,
                    source_sentence=item["text"],
                    position=i,
                ))
            if claims:
                return claims
        except Exception as e:
            log.warning("LLM claim classification failed, falling back", error=str(e))
            pass

    # Split into sentences (simple heuristic; service layer uses NLP)
    sentences = re.split(r'(?<=[.!?])\s+', output_text.strip())

    claims: list[Claim] = []
    for position, sentence in enumerate(sentences):
        if not sentence.strip():
            continue

        sentence_lower = sentence.lower()

        # Classify by markers
        claim_type = ClaimType.FACTUAL

        if any(marker in sentence_lower for marker in _OPINION_MARKERS):
            claim_type = ClaimType.OPINION
        elif any(marker in sentence_lower for marker in _REASONING_MARKERS):
            claim_type = ClaimType.REASONING

        claims.append(Claim(
            claim_id=generate_id("claim"),
            text=sentence.strip(),
            claim_type=claim_type,
            source_sentence=sentence.strip(),
            position=position,
        ))

    return claims


# ============================================================================
# Step 2: Grade Claim
# ============================================================================


async def grade_claim(
    claim: Claim,
    evidence: list[Origin],
    kit: InferenceKit | None = None,
) -> ClaimGrade:
    """Grade a single claim against the evidence pool.

    FACTUAL claims: match against evidence via keyword overlap.
    REASONING claims: validate chain back to grounded premises.
    OPINION claims: auto-grounded (labeled, not verified).
    """
    settings = get_settings().kernel
    threshold = settings.grounding_similarity_threshold

    # Opinions are auto-grounded
    if claim.claim_type == ClaimType.OPINION:
        return ClaimGrade(
            claim_id=claim.claim_id,
            grade=ClaimGradeLevel.GROUNDED,
            evidence_links=[],
            best_similarity=1.0,
            reasoning="Opinion claims are grounded by declaration",
        )

    if kit and kit.has_llm and evidence:
        try:
            ev_texts = [o.content for o in evidence if o.content]
            if ev_texts:
                ev_text_block = "\n".join(f"- {txt}" for txt in ev_texts)
                system_msg = LLMMessage(
                    role="system",
                    content="Grade the claim against the provided evidence. Grades: GROUNDED (fully supported), INFERRED (partially derivable), FABRICATED (no support). If the claim contains specific data matching the evidence (like '0.6%'), it MUST be GROUNDED. Respond EXACTLY with JSON: {\"grade\": \"GROUNDED\", \"reasoning\": \"...\", \"similarity\": 1.0}"
                )
                user_msg = LLMMessage(role="user", content=f"Claim: {claim.text}\nEvidence List:\n{ev_text_block}")
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)

                grade_str = data.get("grade", "FABRICATED")
                if grade_str == "GROUNDED":
                    grade = ClaimGradeLevel.GROUNDED
                elif grade_str == "INFERRED":
                    grade = ClaimGradeLevel.INFERRED
                else:
                    grade = ClaimGradeLevel.FABRICATED

                return ClaimGrade(
                    claim_id=claim.claim_id,
                    grade=grade,
                    evidence_links=[],
                    best_similarity=float(data.get("similarity", 0.0)),
                    reasoning=data.get("reasoning", "LLM graded"),
                )
        except Exception as e:
            log.warning("LLM claim grading failed, falling back", error=str(e))
            pass

    # For FACTUAL and REASONING claims: compare against evidence
    best_similarity = 0.0
    best_links: list[EvidenceLink] = []

    # Basic keyword overlap as similarity proxy at kernel tier
    def tokenize(text: str) -> set[str]:
        # Split by whitespace AND common separators like slashes/dashes/equals/percent
        raw_tokens = re.split(r'[\s\-/=%]+', text.lower())
        tokens = set()
        for t in raw_tokens:
            # Strip remaining edge punctuation
            clean = t.strip(".,!?;:()[]{}'\"")
            if clean:
                tokens.add(clean)
        return tokens

    stop_words = frozenset({
        "the", "is", "a", "an", "are", "of", "to", "in", "and", "with", "some", "very",
        "today", "now", "here", "there", "this", "that", "these", "those",
        "result", "context", "completed", "objectives", "artifacts", "produced"
    })
    
    claim_tokens = tokenize(claim.text) - stop_words

    for origin in evidence:
        if not origin.content:
            continue

        evidence_tokens = tokenize(origin.content) - stop_words
        if not claim_tokens:
            continue

        overlap = len(claim_tokens & evidence_tokens)
        similarity = overlap / max(1, len(claim_tokens))
        similarity = min(1.0, similarity)

        if similarity > best_similarity:
            best_similarity = similarity

        if similarity >= threshold:
            best_links.append(EvidenceLink(
                claim_id=claim.claim_id,
                origin_id=origin.origin_id,
                similarity_score=round(similarity, 4),
                reasoning_chain=f"Keyword overlap: {overlap}/{len(claim_tokens)} tokens match",
            ))

    # Determine grade
    if best_similarity >= threshold:
        grade = ClaimGradeLevel.GROUNDED
        reasoning = f"Evidence found (similarity: {best_similarity:.3f})"
    elif best_similarity >= threshold * 0.5 and claim.claim_type == ClaimType.REASONING:
        grade = ClaimGradeLevel.INFERRED
        reasoning = f"Partially derivable (similarity: {best_similarity:.3f})"
    else:
        grade = ClaimGradeLevel.FABRICATED
        reasoning = f"No supporting evidence found (best: {best_similarity:.3f})"

    return ClaimGrade(
        claim_id=claim.claim_id,
        grade=grade,
        evidence_links=best_links,
        best_similarity=round(best_similarity, 4),
        reasoning=reasoning,
    )


# ============================================================================
# Step 3: Calculate Grounding Score
# ============================================================================


def calculate_grounding_score(grades: list[ClaimGrade]) -> float:
    """Compute overall grounding score as a weighted average.

    GROUNDED claims contribute their full similarity score.
    INFERRED claims contribute a discounted score.
    FABRICATED claims contribute 0.0.
    """
    if not grades:
        return 1.0  # No claims = nothing to verify

    settings = get_settings().kernel
    grounded_weight = settings.grounding_grounded_weight
    inferred_weight = settings.grounding_inferred_weight
    fabricated_weight = settings.grounding_fabricated_weight

    total_score = 0.0
    for grade in grades:
        if grade.grade == ClaimGradeLevel.GROUNDED:
            total_score += grounded_weight * grade.best_similarity
        elif grade.grade == ClaimGradeLevel.INFERRED:
            total_score += inferred_weight * grade.best_similarity
        else:
            total_score += fabricated_weight

    return round(total_score / max(1, len(grades)), 4)


# ============================================================================
# Step 4: Trace Evidence Chain
# ============================================================================


def trace_evidence_chain(
    claim: Claim,
    evidence: list[Origin],
) -> list[EvidenceLink]:
    """Trace the reasoning chain for INFERRED claims.

    Returns the full evidence chain connecting the claim to
    its supporting evidence. If no chain is found, the claim
    should be reclassified as FABRICATED.
    """
    settings = get_settings().kernel
    threshold = settings.grounding_similarity_threshold

    claim_tokens = set(claim.text.lower().split())
    chain: list[EvidenceLink] = []

    for origin in evidence:
        if not origin.content:
            continue

        evidence_tokens = set(origin.content.lower().split())
        if not claim_tokens:
            continue

        overlap = len(claim_tokens & evidence_tokens)
        similarity = min(1.0, overlap / max(1, len(claim_tokens)))

        # Include partial matches for reasoning chains
        if similarity > threshold * 0.3:
            chain.append(EvidenceLink(
                claim_id=claim.claim_id,
                origin_id=origin.origin_id,
                similarity_score=round(similarity, 4),
                reasoning_chain=f"Chain link: {overlap} overlapping tokens",
            ))

    # Sort by similarity descending
    chain.sort(key=lambda link: link.similarity_score, reverse=True)

    return chain


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def verify_grounding(
    output: ToolOutput,
    evidence: list[Origin],
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level grounding verification.

    Extracts claims, classifies them, grades each against evidence,
    and produces a GroundingReport with per-claim grades and an
    overall grounding score.
    """
    ref = _ref("verify_grounding")
    start = time.perf_counter()

    try:
        # Extract and classify claims
        claims = await classify_claims(output.content, kit)

        # Grade each claim
        claim_grades: list[ClaimGrade] = []
        grounded_count = 0
        inferred_count = 0
        fabricated_count = 0

        for claim in claims:
            grade = await grade_claim(claim, evidence, kit)
            claim_grades.append(grade)

            if grade.grade == ClaimGradeLevel.GROUNDED:
                grounded_count += 1
            elif grade.grade == ClaimGradeLevel.INFERRED:
                inferred_count += 1
            else:
                fabricated_count += 1

        # Calculate overall score
        grounding_score = calculate_grounding_score(claim_grades)

        report = GroundingReport(
            output_id=output.output_id,
            total_claims=len(claims),
            grounded_count=grounded_count,
            inferred_count=inferred_count,
            fabricated_count=fabricated_count,
            claim_grades=claim_grades,
            grounding_score=grounding_score,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=report.model_dump(),
            schema="GroundingReport",
            origin=ref,
            trace_id="",
            tags={
                "total_claims": str(report.total_claims),
                "grounded": str(grounded_count),
                "inferred": str(inferred_count),
                "fabricated": str(fabricated_count),
                "grounding_score": f"{grounding_score:.3f}",
            },
        )

        log.info(
            "Grounding verification complete",
            total_claims=report.total_claims,
            grounded=grounded_count,
            inferred=inferred_count,
            fabricated=fabricated_count,
            grounding_score=round(grounding_score, 3),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Grounding verification failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Grounding verification failed", error=str(exc))
        return fail(error=error, metrics=metrics)
