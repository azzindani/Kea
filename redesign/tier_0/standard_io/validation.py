"""
Kernel Standard I/O — Validation Functions.

Validates that Signals and Results conform to the protocol conventions.
Called at tier boundaries to catch malformed data early.

Well-behaved modules should never produce invalid Signals or Results,
but these validators serve as defensive checks at integration points.
"""

from __future__ import annotations

from .errors import input_error
from .types import (
    KernelError,
    ModuleRef,
    Result,
    ResultStatus,
    Signal,
    SignalKind,
)


_VALIDATOR_SOURCE = ModuleRef(tier=0, module="validation", function="validate")


# ============================================================================
# Body Convention Requirements
# ============================================================================

# Maps each SignalKind to its required body keys
_BODY_REQUIREMENTS: dict[SignalKind, list[str]] = {
    SignalKind.TEXT: ["text"],
    SignalKind.DATA: ["data", "schema"],
    SignalKind.FILE: ["file_id", "file_type"],
    SignalKind.COMMAND: ["action", "target"],
    SignalKind.STREAM: ["chunk", "sequence", "final"],
}


# ============================================================================
# Signal Validation
# ============================================================================


def validate_signal(signal: Signal) -> Signal | KernelError:
    """Validate that a Signal's body matches the conventions for its kind.

    Checks:
        - TEXT signals have "text" key
        - DATA signals have "data" and "schema" keys
        - FILE signals have "file_id" and "file_type" keys
        - COMMAND signals have "action" and "target" keys
        - STREAM signals have "chunk", "sequence", and "final" keys

    Args:
        signal: The Signal to validate.

    Returns:
        The signal unchanged if valid, or a KernelError if body
        conventions are violated.
    """
    required_keys = _BODY_REQUIREMENTS.get(signal.kind, [])
    missing_keys = [key for key in required_keys if key not in signal.body]

    if missing_keys:
        return input_error(
            message=(
                f"Signal(kind={signal.kind.value}) body missing required keys: "
                f"{missing_keys}. Expected: {required_keys}, got: {list(signal.body.keys())}"
            ),
            source=_VALIDATOR_SOURCE,
            detail={
                "signal_id": signal.id,
                "signal_kind": signal.kind.value,
                "missing_keys": missing_keys,
                "present_keys": list(signal.body.keys()),
            },
        )

    # Type checks for specific kinds
    if signal.kind == SignalKind.TEXT and not isinstance(signal.body["text"], str):
        return input_error(
            message=f"Signal(kind=TEXT) body['text'] must be str, got {type(signal.body['text']).__name__}",
            source=_VALIDATOR_SOURCE,
            detail={"signal_id": signal.id, "text_type": type(signal.body["text"]).__name__},
        )

    if signal.kind == SignalKind.STREAM:
        if not isinstance(signal.body["sequence"], int):
            return input_error(
                message=f"Signal(kind=STREAM) body['sequence'] must be int, got {type(signal.body['sequence']).__name__}",
                source=_VALIDATOR_SOURCE,
                detail={"signal_id": signal.id},
            )
        if not isinstance(signal.body["final"], bool):
            return input_error(
                message=f"Signal(kind=STREAM) body['final'] must be bool, got {type(signal.body['final']).__name__}",
                source=_VALIDATOR_SOURCE,
                detail={"signal_id": signal.id},
            )

    return signal


# ============================================================================
# Result Validation
# ============================================================================


def validate_result(result: Result) -> Result | KernelError:
    """Validate Result consistency.

    Checks:
        - ERROR status must have a non-None error
        - OK status must not have an error
        - PARTIAL must have both signals and error
        - SKIP must have empty signals
        - All contained signals pass validate_signal()

    Args:
        result: The Result to validate.

    Returns:
        The result unchanged if valid, or a KernelError if inconsistent.
    """
    # Status-specific consistency checks
    if result.status == ResultStatus.ERROR and result.error is None:
        return input_error(
            message="Result with status=ERROR must have a non-None error field",
            source=_VALIDATOR_SOURCE,
            detail={"status": result.status.value},
        )

    if result.status == ResultStatus.OK and result.error is not None:
        return input_error(
            message="Result with status=OK must not have an error field",
            source=_VALIDATOR_SOURCE,
            detail={"status": result.status.value, "error_code": result.error.code},
        )

    if result.status == ResultStatus.PARTIAL:
        if not result.signals:
            return input_error(
                message="Result with status=PARTIAL must have at least one signal",
                source=_VALIDATOR_SOURCE,
                detail={"status": result.status.value, "signal_count": len(result.signals)},
            )
        if result.error is None:
            return input_error(
                message="Result with status=PARTIAL must have a non-None error field",
                source=_VALIDATOR_SOURCE,
                detail={"status": result.status.value},
            )

    if result.status == ResultStatus.SKIP and result.signals:
        return input_error(
            message="Result with status=SKIP must have empty signals",
            source=_VALIDATOR_SOURCE,
            detail={"status": result.status.value, "signal_count": len(result.signals)},
        )

    # Validate all contained signals
    for signal in result.signals:
        validation = validate_signal(signal)
        if isinstance(validation, KernelError):
            return input_error(
                message=f"Result contains invalid signal: {validation.message}",
                source=_VALIDATOR_SOURCE,
                detail={
                    "invalid_signal_id": signal.id,
                    "inner_error_code": validation.code,
                },
            )

    return result
