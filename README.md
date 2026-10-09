# Uptime Monitor

A production-style website uptime monitor (a mini UptimeRobot/Pingdom) built with Python, PostgreSQL, Docker, and AWS.

> 🚧 Work in progress — currently on **Phase 1: Local foundation**.

## Planned architecture
- **api/** — Python (FastAPI) REST API (monitor CRUD, check history, incidents, uptime %, p95 latency)
- **worker/** — Python asyncio checker service (concurrent HTTP checks, incident detection, alerts)
- **frontend/** — React + TypeScript dashboard
- **db/migrations/** — SQL migrations
- **terraform/** — AWS infrastructure (VPC, ECS Fargate, RDS, ALB, SNS, CloudWatch)
- **.github/workflows/** — CI/CD (test → build → push to ECR → deploy to ECS)

## Design decisions
_To be filled in as each phase is built._
