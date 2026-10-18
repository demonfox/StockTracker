---
name: debug-python
description: Systematically diagnoses and fixes bugs in this Python application. Use for errors, regressions, failing tests, unexpected behavior, and performance problems.
---

# Python Debugging Workflow

1. Understand the reported symptom.
2. Identify the relevant execution path.
3. Reproduce the problem whenever possible.
4. Gather evidence before changing code.
5. Form a specific root-cause hypothesis.
6. Test the hypothesis.
7. Implement the smallest appropriate fix.
8. Add or update a regression test.
9. Run the relevant test suite.
10. Explain:
   - root cause
   - fix
   - verification performed

Do not make speculative code changes without evidence.
Do not apply several unrelated fixes simultaneously.

