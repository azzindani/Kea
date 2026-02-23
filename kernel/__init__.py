"""
Kea Human Kernel — Core Processing and Cognitive Engines.

This package contains the implementation of Tier 1+ kernel modules:
    - classification/     → T1: Signal classification and intention detection
    - decomposition/      → T2: Task decomposition and curiosity engines
    - orchestration/      → T3: Workflow building and DAG assembly
    - ooda/               → T4: Observe-Orient-Decide-Act execution loop
    - lifecycle/          → T5: Autonomous ego and lifecycle controller
    - observer/           → T6: Conscious observer (metacognition)

Each module directory contains its own logic and exposes functions that
accept Signal(s) and return Result. All modules use the shared.standard_io
protocol for communication.

Directory naming uses MODULE NAMES, not tier numbers.
Tier-to-module mapping is documented in redesign/ specs.
"""
