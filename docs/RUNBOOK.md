# Kea Research Engine - Operations Runbook

## Quick Reference

| Action | Command |
|--------|---------|
| Check health | `curl /health/full` |
| View logs | `kubectl logs -l app=kea` |
| Restart pods | `kubectl rollout restart deployment/<name>` |
| Scale | `kubectl scale deployment/<name> --replicas=N` |

---

## Incident Response

### Service Down

1. **Check pod status**
   ```bash
   kubectl get pods -l app=kea
   ```

2. **Check logs**
   ```bash
   kubectl logs -l app=kea,component=api-gateway --tail=100
   ```

3. **Check resources**
   ```bash
   kubectl top pods -l app=kea
   ```

4. **Restart if needed**
   ```bash
   kubectl rollout restart deployment/api-gateway
   ```

### High Error Rate

1. **Check error metrics**
   ```
   kea_errors_total
   ```

2. **Check recent logs**
   ```bash
   kubectl logs -l app=kea --since=10m | grep ERROR
   ```

3. **Check dependencies**
   ```bash
   curl /health/full
   ```

### Database Issues

1. **Check connection**
   ```bash
   kubectl exec -it <pod> -- python -c "from shared.database import get_database_pool; import asyncio; print(asyncio.run(get_database_pool().health_check()))"
   ```

2. **Check pool exhaustion**
   ```
   kea_health_database_pool_free
   ```

3. **Increase pool size** (update env vars)

### High Latency

1. **Check percentiles**
   ```
   histogram_quantile(0.95, rate(kea_research_duration_seconds_bucket[5m]))
   ```

2. **Check cache hit rate**
   ```
   rate(kea_cache_hits_total[5m]) / (rate(kea_cache_hits_total[5m]) + rate(kea_cache_misses_total[5m]))
   ```

3. **Scale up**
   ```bash
   kubectl scale deployment/orchestrator --replicas=4
   ```

---

## Common Operations

### Deploy New Version

```bash
# 1. Build
docker build -t kea/api-gateway:v1.2.3 .

# 2. Push
docker push kea/api-gateway:v1.2.3

# 3. Update deployment
kubectl set image deployment/api-gateway api-gateway=kea/api-gateway:v1.2.3

# 4. Watch rollout
kubectl rollout status deployment/api-gateway
```

### Rollback

```bash
kubectl rollout undo deployment/api-gateway
```

### Run Migrations

```bash
kubectl exec -it <api-gateway-pod> -- alembic upgrade head
```

### Clear Cache

```bash
kubectl exec -it <redis-pod> -- redis-cli FLUSHDB
```

### Rotate Secrets

```bash
# 1. Create new secret
kubectl create secret generic kea-secrets-new --from-literal=jwt-secret='new-secret'

# 2. Update deployment
kubectl set env deployment/api-gateway --from=secret/kea-secrets-new

# 3. Delete old secret
kubectl delete secret kea-secrets
```

---

## Alerts and Actions

| Alert | Severity | Action |
|-------|----------|--------|
| APIGatewayDown | Critical | Check pod, restart |
| OrchestratorDown | Critical | Check pod, restart |
| HighErrorRate | Warning | Check logs, investigate |
| SlowResearch | Warning | Check resources, scale |
| DatabasePoolExhausted | Warning | Increase pool, scale |
| HighMemoryUsage | Warning | Check for leaks, restart |
| PossibleBruteForce | Critical | Block IP, investigate |
| CircuitBreakerOpen | Critical | Check downstream service |

---

## Monitoring Dashboards

### Key Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Error rate | <1% | 1-5% | >5% |
| P95 latency | <5s | 5-30s | >30s |
| Cache hit rate | >60% | 30-60% | <30% |
| Memory usage | <70% | 70-85% | >85% |

### Queries

**Errors by endpoint:**
```promql
sum by (endpoint) (rate(kea_errors_total[5m]))
```

**Research success rate:**
```promql
rate(kea_research_requests_total{status="success"}[5m]) / rate(kea_research_requests_total[5m])
```

---

## Maintenance Windows

### Recommended Schedule

| Task | Frequency |
|------|-----------|
| Log rotation | Daily |
| Database backup | Daily |
| Dependency updates | Weekly |
| Security patches | Immediate |
| Load testing | Monthly |

### Pre-maintenance Checklist

1. [ ] Notify stakeholders
2. [ ] Create database backup
3. [ ] Document current state
4. [ ] Prepare rollback plan

### Post-maintenance Checklist

1. [ ] Verify health checks
2. [ ] Check error rates
3. [ ] Update documentation
4. [ ] Notify completion

---

## Contacts

| Role | Contact |
|------|---------|
| On-call | oncall@example.com |
| Database | dba@example.com |
| Security | security@example.com |
