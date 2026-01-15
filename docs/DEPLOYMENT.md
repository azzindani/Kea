# Kea Research Engine - Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for production)
- PostgreSQL 16+
- Redis 7+
- Qdrant (optional, for RAG)

---

## Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/kea.git
cd kea
cp .env.example .env
# Edit .env with your API keys
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e ".[dev]"
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

Services:
- API Gateway: http://localhost:8080
- Orchestrator: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### 4. Run Migrations

```bash
alembic upgrade head
```

---

## Production Deployment

### Option A: Kubernetes

#### 1. Create Secrets

```bash
kubectl create secret generic kea-secrets \
  --from-literal=database-url='postgresql://user:pass@host/db' \
  --from-literal=jwt-secret='your-32-char-secret-minimum!' \
  --from-literal=openrouter-api-key='sk-or-xxx'
```

#### 2. Deploy

```bash
kubectl apply -f k8s/
```

#### 3. Verify

```bash
kubectl get pods -l app=kea
kubectl logs -l app=kea,component=api-gateway
```

### Option B: Docker Compose

```bash
export ENVIRONMENT=production
docker-compose -f docker-compose.yml up -d
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | development | dev/staging/production |
| `DATABASE_URL` | Yes (prod) | sqlite | PostgreSQL URL |
| `JWT_SECRET` | Yes (prod) | generated | Min 32 chars |
| `OPENROUTER_API_KEY` | Yes | - | LLM API key |
| `REDIS_URL` | No | - | Redis URL |
| `QDRANT_URL` | No | - | Vector DB URL |
| `CORS_ORIGINS` | No | * | Comma-separated origins |

---

## Health Checks

```bash
# Basic
curl http://localhost:8000/health

# Full (checks all dependencies)
curl http://localhost:8000/health/full
```

---

## Scaling

### Horizontal

```yaml
# k8s/deployments.yaml
spec:
  replicas: 4  # Increase replicas
```

### Resource Limits

| Environment | API Gateway | Orchestrator |
|-------------|-------------|--------------|
| Dev | 256Mi | 512Mi |
| Prod | 512Mi-1Gi | 1Gi-4Gi |

---

## Monitoring

### Prometheus Metrics

Available at `/metrics`:
- `kea_auth_attempts_total`
- `kea_research_duration_seconds`
- `kea_errors_total`

### Grafana Dashboards

Import dashboards from `configs/grafana/`

### Alerts

Configure in Prometheus:
```yaml
rule_files:
  - /etc/prometheus/alerts.yml
```

---

## Backup Strategy

### Database

```bash
pg_dump -h host -U user -d kea > backup.sql
```

### Restore

```bash
psql -h host -U user -d kea < backup.sql
```

---

## SSL/TLS

### With Ingress (recommended)

```yaml
# k8s/services.yaml
spec:
  tls:
    - hosts:
        - api.kea.example.com
      secretName: kea-tls
```

### With cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

---

## Troubleshooting

### Pod not starting

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Database connection failed

1. Check `DATABASE_URL` format
2. Verify network connectivity
3. Check credentials

### Rate limiting issues

Check headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
```

Increase limit via `RATE_LIMIT_PER_MINUTE` env var.
