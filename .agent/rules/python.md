# Python Engineering Rules

Use Python 3.12+ conventions unless the existing project specifies otherwise.

## Code quality

- Prefer simple, readable Python over clever implementations.
- Use type hints for public functions and methods.
- Keep functions small and focused on one responsibility.
- Avoid unnecessary abstractions.
- Do not introduce new dependencies unless clearly justified.
- Follow existing project structure and naming conventions.

## Error handling

- Never silently swallow exceptions.
- Catch specific exception types rather than Exception when possible.
- Produce actionable error messages.
- Log unexpected failures with sufficient context.

## Dependencies

- Reuse existing project dependencies whenever possible.
- Before introducing a dependency, explain why the standard library or an existing dependency is insufficient.

## Security

- Never hard-code secrets, passwords, API keys, or credentials.
- Read secrets from environment variables or the configured secret-management system.
- Validate external input at trust boundaries.

## Changes

Before modifying an existing implementation:
1. Understand the relevant code path.
2. Identify existing tests.
3. Make the smallest change that solves the problem.
4. Run the relevant tests.
5. Run linting/type checking when appropriate.

