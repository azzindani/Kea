# ☸️ Kubernetes Manifests

This directory contains the Kubernetes (K8s) configuration files for deploying the Kea ecosystem to a cluster (e.g., GKE, EKS, or Minikube).

## 🚀 Deployment

To apply the configuration to your cluster:

```bash
# Apply ConfigMaps and Secrets first
kubectl apply -f config.yaml

# Deploy Services (Networking)
kubectl apply -f services.yaml

# Deploy Applications (Pods/replicas)
kubectl apply -f deployments.yaml
```

## 📁 Codebase Structure

- **`config.yaml`**: Contains `ConfigMaps` and `Secrets`.
    - `kea-config`: Environment variables like `DB_HOST`, `REDIS_URL`.
    - `kea-secrets`: Sensitive keys (API tokens) - *Note: Use SealedSecrets or Vault in production*.
- **`services.yaml`**: Defines the K8s `Service` objects (ClusterIP, LoadBalancer) that expose the pods to the internal network.
    - `gateway-service`: Exposes port 8000.
    - `orchestrator-service`: Exposes port 8001.
    - etc.
- **`deployments.yaml`**: Defines the `Deployment` objects (replicas, containers, images).
    - `kea-gateway`: running `services.api_gateway.main:app`
    - `kea-orchestrator`: running `services.orchestrator.main:app`
    - `kea-worker`: running `workers.research_worker` (background scalers)

## 🏗️ Architecture

The deployment follows a **Microservices Topology**:
- **Gateway** is the only service typically exposed via Ingress or LoadBalancer.
- **Internal Services** (Orchestrator, RAG, Vault) communicate via ClusterIP DNS names (e.g., `http://orchestrator-service:8001`).
- **Postgres** and **Redis** are assumed to be managed services or deployed via separate Helm charts (not included here).
