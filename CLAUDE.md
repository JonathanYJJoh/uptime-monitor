# Project: Website Uptime Monitor (AWS + Docker + PostgreSQL)

## About the developer
- Jonathan: UC Berkeley Statistics & Data Science student (class of 2028).
- Was a Software Engineering Intern at Pextra (private cloud), writing MCP tools in Go that call REST APIs. Before that, an IT Infrastructure Intern (VoIP and network troubleshooting).
- Main language is Python. Also knows Go, TypeScript/React, and basic SQL. Still learning AWS, Docker, Terraform, and CI/CD, so explain cloud concepts as they come up.
- Works on Windows with Docker Desktop + WSL2.

## Goal
A production-style uptime monitor (a mini UptimeRobot/Pingdom) that shows he can design and deploy systems on AWS with Docker and PostgreSQL, and that he can honestly put on a resume. Learning matters as much as finishing.

## What the app does
- Monitors: URL, check interval (e.g. 60s), timeout, expected HTTP status.
- The worker checks each monitor on schedule and records the status code, response time (ms), success, error, and SSL expiry.
- Incidents: DOWN after 3 consecutive failures, UP again on recovery. Each one has a start, an end, and a duration.
- Alerts (SNS email): on down, on recovery, and when an SSL cert expires within 14 days.
- Stats: uptime % (24h/7d/30d), average and p95 response time.
- Dashboard: monitors with status, uptime %, a response-time chart, and incident history.
- Retention: delete raw checks older than 30 days.

## Tech stack
- Backend: Python 3.13 (his main language; switched from Go on 2026-10-08). The API (FastAPI) and the checker worker are two separate services. The worker uses asyncio + httpx for concurrent checks.
- DB: PostgreSQL via psycopg 3 (plain SQL, no ORM, so he learns the SQL). Migrations are plain .sql files in db/migrations, run with the language-agnostic `migrate/migrate` Docker image.
- Tests: pytest.
- Frontend: React + TypeScript (built last).
- Local: Docker Compose (postgres, api, worker, frontend).
- AWS: VPC (public + private subnets), ECS Fargate, ECR, RDS Postgres, ALB, SNS, CloudWatch, IAM, and Secrets Manager or SSM.
- IaC: Terraform. CI/CD: GitHub Actions (test, build, push to ECR, deploy to ECS).

## Tables (starting point)
- monitors: id, name, url, interval_seconds, timeout_ms, expected_status, is_active, created_at
- checks: id, monitor_id, checked_at, status_code, response_time_ms, success, error, ssl_expires_at
- incidents: id, monitor_id, started_at, resolved_at, cause

## Build phases (finish each before moving on)
1. Local foundation: Compose with Postgres + migrations. Done when the tables exist and he can insert and query a monitor.
2. Checker worker: loads active monitors, checks them concurrently, saves results, handles timeouts. Done when checks appear in the DB every interval.
3. Incidents + alerts: the 3-failure rule, recovery, SSL warnings (logged locally first). Done when a test site going down opens an incident and recovery closes it.
4. REST API: monitor CRUD, check history, incidents, uptime %, p95. Done when everything is manageable with curl/Postman.
5. AWS with Terraform: VPC, RDS (private subnet), ECR, ECS Fargate, ALB, SNS, CloudWatch logs. Done when it runs fully on AWS and emails on downtime.
6. CI/CD + observability: GitHub Actions, CloudWatch custom metrics, and an alarm if the worker stops. Done when a git push deploys automatically.
7. Dashboard + polish: React dashboard, unit tests (checker, uptime math), README with an architecture diagram and design decisions.

## AWS cost rules (student budget)
- Remind him to set an AWS billing alarm before creating anything.
- Use the smallest sizes (db.t4g.micro or db.t3.micro, minimal Fargate CPU/memory).
- No NAT Gateways: run Fargate in public subnets with locked-down security groups, and keep RDS private.
- Warn before anything that costs money. Remind him to run `terraform destroy` when the stack isn't in use.

## How to help
- Teach, don't dump code. Explain what we're doing and why before writing it, especially for AWS, networking, Docker, and Terraform.
- Work one phase and one small step at a time. Never write the whole project at once.
- When reasonable, let him write the code first, then review it.
- Point out real-world design decisions he can explain in interviews.
- Suggest clear git commit points after each step.
- Keep resume claims honest: write bullets only about what was actually built, with real numbers.

## Progress
- [ ] Phase 1: Local foundation
  - [x] Repo skeleton (2026-10-07)
  - [x] Step 1a: Postgres 17 running in Compose with a healthcheck and named volume (2026-10-09)
  - [ ] Step 1b: first migration (he writes it; I review)
  - [ ] Step 1c: insert and query a monitor
