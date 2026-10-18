---
name: deploy-gcp
description: Prepares and deploys this application to Google Cloud using the project's approved deployment architecture.
---

# GCP Deployment

Before deployment:

1. Run tests.
2. Verify required environment variables.
3. Verify the configured GCP project and region.
4. Never expose credentials in source files.
5. Show potentially destructive commands before executing them.

For production deployments:
- prefer reproducible deployment configuration
- avoid manual server modifications that are not captured in source control
- verify application health after deployment
- inspect deployment logs on failure

