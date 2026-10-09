# Feedback Desk documentation

These documents describe the current product and delivery boundaries. Earlier speculative hosting research and superseded scenarios are preserved under [archive](archive/README.md), outside the current setup and architecture guidance.

| Document                                       | Purpose                                                 |
| ---------------------------------------------- | ------------------------------------------------------- |
| [Overview](overview.md)                        | Product scope and a short walkthrough.                  |
| [Architecture](architecture.md)                | Runtime boundaries, source tree and data flow.          |
| [Setup](setup.md)                              | Local startup, toolchain and environment variables.     |
| [API and Swagger](api.md)                      | Routes, authentication, cursors and interactive schema. |
| [Authentication and tenancy](auth-tenancy.md)  | Session ownership, isolation and retention.             |
| [Workflows](workflows.md)                      | State transitions, transactions and recovery.           |
| [Testing](testing.md)                          | Commands, mirrored test tree and evidence boundaries.   |
| [Operations and deployment](operations.md)     | Vercel, Docker, rollout, rollback and backups.          |
| [Limits](limits.md)                            | Enforced budgets and unsupported guarantees.            |
| [Delivery status](delivery-status.md)          | Implemented, verified, deployed and pending work.       |
| [Current delivery plan](../planning/README.md) | Epics, stories and individual task records.             |
| [Historical archive](archive/README.md)        | Preserved earlier plans, research and style samples.    |

Status belongs in [delivery status](delivery-status.md) and the [plan](../planning/README.md). Do not infer remote deployment, hosted CI or restore success from source files alone.
