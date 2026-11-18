# K1S – Kubernetes Infrastructure with gRPC

> Lightweight Python gRPC microservices on Kubernetes

## 🎯 GoatGambling Project

First-person gambling game: players bet against a goat croupier.

**Mechanics**:
- Start: 10 blades of grass
- Action: Skip (record score) or bet 1 to N/2 grass
- Odds: Lose (3/6) | Win ×1.25 (1/6) | Win ×1.5 (1/6) | Win ×2 (1/6)
- Leaderboard: Max 10 scores

## 🛠 Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Astro |
| Backend | Python 3.8+ gRPC services |
| Build | Buildx + BuildKit |
| Deploy | Argo Workflows → Kubernetes |
| Quality | Ruff, pytest |

## 🚀 Quick Start

Requires Python 3.8+, Node 18+ and curl.

```bash
./quickstart.sh   # installs, builds, starts everything → http://localhost:4321
```

Ctrl+C stops all services. Ports: `PORT` (site, default 4321), `GATEWAY_PORT` (HTTP API, default 8080).

### Setup

```bash
# 1. Check requirements
python scripts/course.py prerequisites

# 2. Create virtual environment
python scripts/course.py setup-venv
source .venv/bin/activate  # Linux/macOS or .venv\Scripts\activate on Windows
```

### Development

```bash
# Generate gRPC stubs from .proto files
python scripts/course.py generate-grpc

# Run tests & linting
python scripts/course.py test
python scripts/course.py lint

# Full verification (all checks)
python scripts/course.py verify
```

### Build & Deploy

```bash
# Local build (development)
python scripts/course.py build-local

# Multi-platform build & push (CI/CD)
python scripts/course.py build

# Deploy with Argo
python scripts/course.py validate-workflows
python scripts/course.py deploy
python scripts/course.py watch
```

## 📂 Project Structure

```
apps/
├── game-service/           # Game logic (Python gRPC)
├── leaderboard-service/    # Score management (Python gRPC)
├── api-gateway/            # gRPC clients + HTTP API for the frontend (Python)
└── frontend/               # Astro SSR: menu (/) + pseudo-3D game table (/play), proxies /api/* to the gateway

quickstart.sh               # Run the whole stack locally

.argo/workflows/            # Kubernetes Argo Workflows
.venv/                      # Python virtual environment (auto-created)
```

## 📋 Commands Reference

| Command | Purpose |
|---------|---------|
| `prerequisites` | Verify Python, buildx, kubectl, argo |
| `setup-venv` | Create `.venv` with dependencies |
| `generate-grpc` | Compile `.proto` → Python stubs |
| `test` | Run pytest on all services |
| `lint` | Run Ruff linting |
| `verify` | Full QA gate (test + lint + supply-chain) |
| `build-local` | Build images locally |
| `build` | Build & push multi-platform images |
| `validate-workflows` | Validate Argo YAML syntax |
| `deploy` | Submit Argo Workflow to cluster |
| `watch` | Monitor Workflow execution |

## 🔧 Configuration

### Ruff (Python Linting)

Enabled rules: **E** (errors), **F** (pyflakes), **I** (imports)

```bash
python -m ruff check .
python -m ruff format --check .
```

### gRPC Services

Each service has:
- `service.proto` - Service definition (Protocol Buffers)
- `main.py` - gRPC server implementation
- `Dockerfile` - Buildx multi-stage build
- `requirements.txt` - Service dependencies
- `tests/` - pytest test files

**Example proto** (`game.proto`):
```protobuf
syntax = "proto3";
service GameService {
  rpc PlaceBet(BetRequest) returns (BetResponse);
}
message BetRequest { uint32 amount = 1; }
message BetResponse { bool win = 1; uint32 payout = 2; }
```

### Buildx Dockerfile

All Dockerfiles must pin base images to digest:

```dockerfile
FROM python:3.11@sha256:abc123...

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. *.proto

CMD ["python", "main.py"]
```

### Argo Workflows

Workflows in `.argo/workflows/*.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: game-pipeline-
spec:
  entrypoint: build-and-deploy
  templates:
  - name: build-and-deploy
    dag:
      tasks:
      - name: test
        template: run-tests
      - name: build
        template: buildx-build
        depends: test.Succeeded
      - name: deploy
        template: deploy-k8s
        depends: build.Succeeded
```

## 🔐 CI/CD Gates

**Local verification**:
```bash
python scripts/course.py verify
```

Runs (in order):
1. pytest (all services)
2. Ruff linting
3. Supply chain policy (pinned images, action SHAs)

**Branch protection requires**:
- ✅ All tests passing
- ✅ Ruff linting passed
- ✅ No secrets (Gitleaks)
- ✅ Buildx image builds
- ✅ Code review

## 🐛 Common Issues

### Virtual environment not found
```bash
python scripts/course.py setup-venv
```

### gRPC stubs missing
```bash
python scripts/course.py generate-grpc
```

### Ruff violations
```bash
python -m ruff format .  # Auto-fix
python -m ruff check --show-source .  # Details
```

### Buildx not found
```bash
# Docker Desktop: Settings > Experimental Features > Enable
# Or install: brew install --cask docker (macOS)
```

## 🎓 Learning Path

**Phase 1 (10/20 pts)**: Python gRPC service locally
- [ ] Proto file & code generation
- [ ] Unit tests with pytest
- [ ] Dockerfile with multi-stage build
- [ ] Image build with buildx

**Phase 2 (7/20 pts)**: Multi-service orchestration
- [ ] gRPC inter-service communication
- [ ] Kubernetes Deployment manifests
- [ ] Service discovery
- [ ] API Gateway (gRPC router)

**Phase 3 (3/20 pts)**: Production ready
- [ ] Argo Workflow definitions
- [ ] Astro frontend integration
- [ ] CI/CD automation
- [ ] Monitoring & observability

## 📖 Resources

- [gRPC Python](https://grpc.io/docs/languages/python/)
- [Protocol Buffers](https://protobuf.dev)
- [Buildx Docs](https://docs.docker.com/buildx/working-with-buildx/)
- [Argo Workflows](https://argoproj.github.io/argo-workflows/)
- [Kubernetes](https://kubernetes.io/)

## 🏃 For Impatient Developers

```bash
# 5-minute setup
python scripts/course.py prerequisites
python scripts/course.py setup-venv
source .venv/bin/activate
python scripts/course.py verify

# If all green, you're ready to code!
```

---

**Tech Stack**: Python 3.8+, gRPC, Buildx, Argo, Kubernetes  
**Team**: Binôme  
**Status**: EFREI Educational Project