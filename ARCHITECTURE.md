# Architecture

This document describes the high-level architecture of Nodepad.
If you want to familiarize yourself with the codebase, you are in the right place!

## Bird's Eye View

Nodepad is a hierarchical outliner application designed for creating and managing deeply nested lists.
It consists of a **FastAPI** backend and a **React** frontend, coordinated via a REST API.

The core data structure is a **NodeList**, which contains a tree of **Nodes**.
- **Hierarchy**: Represented using both `parent_id` pointers and a materialized `path` (using PostgreSQL `ltree`).
- **Ordering**: Handled via **fractional indexing** (decimal positions), allowing for O(1) insertions between any two nodes.
- **Consistency**: The backend uses a Longest Increasing Subsequence (LIS) algorithm to handle complex subtree movements while maintaining a stable order.

The analyzer (and this documentation) keeps everything in memory; we never do direct IO in the business logic layer.

## Code Map

This section provides a "bird's eye" map of the codebase.

### `backend/app/api/`
FastAPI routes. This is the **API Boundary**. It handles HTTP requests, validates input using Pydantic schemas, and delegates to services.

### `backend/app/services/`
The "brain" of the application. Contains domain logic that is independent of HTTP or Database implementation details.
- `lists.py`: Implements the LIS algorithm and fractional position calculations.

**Architecture Invariant**: Services never handle raw HTTP objects (like `Request` or `BackgroundTasks`) directly. They receive and return pure data.

### `backend/app/models/`
SQLAlchemy models.
- `lists.py`: Defines the `Node` and `NodeList` tables.
- **Invariant**: We use `ltree` for hierarchical queries and `Numeric(30, 15)` for fractional positions to prevent precision loss.

### `frontend/src/routes/`
TanStack Router definitions. This defines the "physical" structure of the application's pages.

### `frontend/src/store/`
Zustand stores. This is the **Client State Boundary**.
- **Invariant**: UI components should read from the store rather than passing deep props.

### `frontend/src/components/`
UI components built with **Tailwind CSS 4** and **Radix UI**.
- **Invariant**: Atomic components (buttons, inputs) are decoupled from application logic.

## Architecture Invariants

- **Unidirectional Data Flow**: Frontend state is updated via actions that trigger API calls, which in turn refresh the local store.
- **Optimistic UI**: The frontend predicts the outcome of reordering actions to ensure a "snappy" keyboard-first experience.
- **PostgreSQL Dependency**: The use of `ltree` means the backend specifically targets PostgreSQL. We do not aim for database-agnosticism.
- **Stateless Backend**: The backend does not maintain server-side sessions. All authentication and authorization are handled via JWTs provided in the `Authorization` header.

## Cross-Cutting Concerns

### Development Workflow
We use **Docker Compose** with a native `watch` feature or local environments.

- **Backend**: Managed with `uv`.
- **Frontend**: Managed with `bun`.

### Testing
- **Backend**: Unit tests using `pytest`.
- **Frontend**: E2E tests using **Playwright**.

### Authentication
We use **OAuth2 with Password Flow** and **JWT** (JSON Web Tokens).
- Tokens are short-lived.
- The `app.core.security` module handles token generation and validation.
- **Invariant**: The backend never stores passwords in plain text; it uses `argon2` or `bcrypt` (via `pwdlib`).
