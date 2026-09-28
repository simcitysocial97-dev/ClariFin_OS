"""Cross-layer integration tests.

Validates end-to-end data flows across layers:
- Frontend hooks → API routes → Services → Repositories → DB
- Schema consistency between frontend (Zod) and backend (Pydantic)
- Financial calculation accuracy across all layers
"""
