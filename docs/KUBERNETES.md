# Kubernetes Deployment

Apply base manifests:

```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secrets.example.yaml  # edit first
kubectl apply -f k8s/base/api-deployment.yaml
kubectl apply -f k8s/base/worker-deployment.yaml
kubectl apply -f k8s/base/api-service.yaml
kubectl apply -f k8s/base/api-hpa.yaml
kubectl apply -f k8s/base/network-policy.yaml
```

Notes:
- `surveillance-secrets` must be replaced with real values.
- API image defaults to `ghcr.io/rohan5commit/trade-surveillance-ai:latest`.
- HPA target is CPU 70%, min 3 pods max 20 pods.
