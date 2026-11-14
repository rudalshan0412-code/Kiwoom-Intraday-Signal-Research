# Public code scope

This repository is a **selected source-code portfolio**, not a complete or deployable trading system.
The original project was developed in September–November 2026, with substantial generative-AI assistance.

## Included

- `modules/event_models.py` — normalized market and order-related event data structures.
- `modules/weekly_data_manager.py` — weekly SQLite snapshots, compression, hashes and archive metadata.
- `ml_pipeline/multihead_model.py` — shared-backbone, four-head PyTorch model definition **without model weights**.
- `ml_pipeline/build_walk_forward_split.py` — time-ordered dataset splitting and summary logic; the original hard-coded server root was replaced with a repository-relative root for portability.
- `tests/test_event_models.py` — synthetic-data checks for event structures. Run with `python -m tests.test_event_models` from the repository root.

## Intentionally omitted

- Trading engine, entry/exit strategy logic, model checkpoints and runtime configuration.
- Raw market data, account data, secrets, credentials, server logs, and research datasets.
- The full real-time parser and its historical demo payload, pending separate strategy/data-use review.
- The complete dataset feature/label generation script, which exposes strategy-specific research decisions.

The selected scripts are **not an end-to-end executable collector, trainer, or backtester**. Their role is to document technical implementation and project structure. Reproducing historical analyses requires private datasets and additional code. There is no audited live-trading capability in this public selection.

No license is included by default. Publication and any grant of reuse rights should be decided separately. A public GitHub repository can still be viewed and forked even without a license; omitting a license is not a technical copy-prevention mechanism.
