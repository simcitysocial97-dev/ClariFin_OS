# Archived Reflex Dashboard

**Status: DEPRECATED**

This directory contains the deprecated Reflex dashboard.

It is no longer part of the active architecture.

## Do NOT:
- Modify this code
- Depend on this code
- Attempt to run this code

## Active Architecture

The current system uses:
- **Frontend**: Next.js (see `/frontend/`)
- **Backend**: FastAPI (see `/backend/src/`)
- **Database**: SQLite (see `/backend/data/`)

## Deprecation Date

February 2026

## Reason

Reflex was removed from the architecture in favor of a cleaner separation:
- Next.js for the frontend (better React ecosystem, more flexible)
- FastAPI for the backend (pure Python API, no framework lock-in)