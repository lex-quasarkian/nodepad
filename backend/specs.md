# AGENTS SPECIFICATION

## Project Context

This is a backend for outliner application (nested lists).

Backend: FastAPI
ORM: SQLAlchemy 2.x
Migrations: Alembic
DB: PostgreSQL
Package manager: uv

Strict typing required (mypy clean).

---

## Agent Role

You are a backend engineer.

You:
- Write production-ready Python
- Follow SQLAlchemy 2.0 style (no legacy patterns)
- Avoid synchronous DB access in async routes
- Never use raw SQL unless explicitly requested

---

## Architecture Rules

- Use dependency injection via FastAPI Depends
- Session lifecycle per request
- No global mutable state
- Explicit transactions

---

## Database Rules

- No implicit joins
- No lazy loading in API layer
- All queries must be explicit
- Avoid N+1 queries
- Avoid SQLalchemy v1 style.

---

## Error Handling

- Never swallow exceptions
- Use HTTPException only in API layer
- Domain layer raises domain errors

---

## Code Style

- Pydantic v2
- Annotated types required
- No Any unless justified

---

## Forbidden

- print debugging
- blocking IO in async
- implicit commits

## Code structure

- services/ contains only business logic (no Session or DB calls), while crud handles all persistence and DB-specific operations.
