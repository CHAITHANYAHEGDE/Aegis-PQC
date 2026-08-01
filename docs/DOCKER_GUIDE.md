# Docker Guide

We provide containerized deployment using Docker and Docker Compose to eliminate "works on my machine" issues and ensure a production-ready environment.

> **Note:** Docker configuration has been prepared but has not yet been validated in a local Docker environment. Users should verify the container build after installing Docker.

## Architecture
The `docker-compose.yml` orchestrates the stack:
- **FastAPI Backend / Benchmark Engine:** Runs the C++ extension and Python ML pipeline.
- *(Future)* **Frontend:** Web UI.

## Building and Running
To launch the complete stack:
```bash
docker compose up --build
```

This multi-stage build will:
1. Compile `liboqs`.
2. Compile `aegis_engine` (pybind11 extension).
3. Install Python dependencies.
4. Launch the FastAPI server on port 8000.

## Health Checks
The FastAPI server includes a `/health` endpoint which Docker polls to determine container readiness.

## Cleaning Up
```bash
docker compose down -v
```
