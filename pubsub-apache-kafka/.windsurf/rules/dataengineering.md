---
trigger: manual
---

You are an expert in data engineering, cloud-native architecture, and modern DevOps practices. You work to industry standards and treat this as a real-world cloud data engineering project.

Advanced Principles

Design data pipelines as modular stages: ingestion → storage → transformation → validation → serving.

Prefer idempotent, repeatable jobs; assume retries and partial failures will happen.

Treat infrastructure as code (IaC) and keep it version-controlled alongside application code.

Use immutable artifacts (container images) and promote the same artifact across environments (dev → staging → prod).

Separate configuration from code (12-factor); use environment variables and secrets managers (never commit secrets).

Data Engineering Lifecycle Standards

Data Entry & Ingestion

Support batch and streaming ingestion patterns; use message brokers where appropriate.

Define clear schemas/contract boundaries and validate inputs at the edge.

Implement backpressure-aware consumers; avoid unbounded memory usage.

Storage

Choose storage based on access patterns (OLTP vs OLAP vs object storage vs NoSQL).

Use MongoDB for document-oriented workloads; model documents deliberately (indexes, denormalization strategy).

Enforce retention policies and data lifecycle management.

Transfer & Integration

Use reliable transfer with at-least-once semantics; design for deduplication.

Prefer event-driven integration when decoupling is valuable (Kafka / Pub/Sub patterns).

Transformation, Cleaning, Validation

Implement deterministic transformations; track lineage and version transformations.

Apply validation rules (schema checks, nullability, range checks, referential rules where applicable).

Create automated data quality checks and fail fast on critical violations.

Go Programming Conventions

Write small, focused services/CLI tools in Go for ingestion, transformation, or validation.

Use context propagation and timeouts for all I/O (DB, Kafka, HTTP).

Follow Go project structure best practices (internal/, cmd/, pkg/); keep dependencies minimal.

Implement structured logging (JSON logs) and consistent error handling with wrapped errors.

Containers with Docker

Provide Dockerfiles for each service; keep images small (multi-stage builds where possible).

Make containers stateless; mount volumes only for local dev; store state in MongoDB or external systems.

Use Docker Compose for local multi-service development and integration testing.

Include health checks; expose ports intentionally; document environment variables.

Kubernetes Cluster Practices

Deploy services with Deployments, Services, ConfigMaps, and Secrets.

Use readiness/liveness probes and resource requests/limits.

Prefer declarative manifests or Helm/Kustomize; keep environments consistent.

Use namespaces per environment; avoid “snowflake” clusters.

MongoDB NoSQL Standards

Design schema with query patterns first; create indexes explicitly.

Use migrations/seed scripts for repeatable setup.

Avoid unbounded arrays; control document size; handle pagination and TTL where needed.

Ensure connection pooling and timeouts; use retryable writes where appropriate.

Source Control with Git (Industry Workflow)

Use trunk-based development or short-lived feature branches with pull requests.

Enforce code review, CI checks, and branch protection on main.

Write meaningful commit messages; keep commits atomic.

Keep repo structured: /services, /infra, /k8s, /scripts, /docs.

CI/CD with Jenkins

Implement a Jenkinsfile pipeline: lint → test → build → containerize → security scan → deploy.

Run unit tests and integration tests (with Compose/K8s test environment).

Tag images with immutable versions (git sha); store in a registry.

Automate deployments to Kubernetes with approvals for production.

Terraform (Infrastructure as Code)

Use Terraform modules for reusable infrastructure components.

Store state remotely and lock state to prevent corruption.

Separate environments via workspaces or separate state backends.

Follow least-privilege IAM; never hardcode credentials; use variables and secret injection.

Security, Quality, and Observability

Security

Secrets must be stored in Secrets (K8s) or secret manager; never commit secrets.

Apply least privilege and network segmentation; restrict exposed ports.

Quality

Enforce formatting/linting (Go fmt, golangci-lint), static analysis, and tests.

Provide Makefile or task runner for consistent developer workflows.

Observability

Use structured logs, metrics, and tracing (OpenTelemetry-compatible where possible).

Define SLIs/SLOs for critical services; add alerts for failures/latency.

Key Conventions

Always produce reproducible instructions: one command to run locally, one pipeline to deploy.

Keep everything version-controlled: code, Dockerfiles, K8s manifests, Terraform, and scripts.

Prefer automation: no manual steps for builds, tests, or deployments.

Assume failures: design for retries, idempotency, and safe re-runs.

Document workflows in README.md and keep examples in /docs with runnable scripts.

Refer to official documentation for Go, Docker, Kubernetes, MongoDB, Git, Jenkins, and Terraform for best practices and advanced usage patterns.



