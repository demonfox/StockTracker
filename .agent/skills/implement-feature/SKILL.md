---
name: implement-feature
description: Implements new application features while preserving existing architecture and testing conventions.
---

# Feature Implementation Workflow

Before coding:

1. Understand the requested behavior.
2. Inspect the relevant existing implementation.
3. Identify architectural patterns already used.
4. Identify affected tests and interfaces.
5. Produce a brief implementation plan.

During implementation:

6. Make incremental changes.
7. Preserve backwards compatibility unless explicitly told otherwise.
8. Add appropriate tests.
9. Avoid unrelated refactoring.

After implementation:

10. Run relevant tests.
11. Run linting/type checking.
12. Review the diff for unnecessary changes.
13. Summarize what changed and any remaining risks.

