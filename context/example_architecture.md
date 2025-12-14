# Software Architecture: Clean Architecture with DDD

## 1. Core Principles
*   **Domain-Driven Design (DDD)**: Focus on the core domain logic.
*   **Separation of Concerns**: UI, Database, and Frameworks should depend on Use Cases, not the other way around.

## 2. Directory Structure Requirement
The solution should loosely follow this structure (even in a single file logic):
*   `Domain`: Entities and Value Objects (Pure Python, no imports).
*   `Application`: Use Cases / Services.
*   `Infrastructure`: Database Adapters, API Clients.

## 3. Class Requirements
*   All entities must be `dataclasses`.
*   Use `typing` for all function signatures.
