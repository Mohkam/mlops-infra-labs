# ☸️ Kubernetes Basic Lab - Nginx Deployment & Service

## ✅ Objectives

- Practice Kubernetes resources in a Minikube environment
- Deploy an Nginx web server as a Deployment and expose it via NodePort

## 📁 Configuration Files

| File | Description |
|------|-------------|
| `nginx-deployment.yaml` | Deployment that creates 2 Nginx Pods |
| `nginx-service.yaml`    | NodePort service exposed externally |

## 🛠️ Run Commands

```bash
# Create resources
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml

# Check deployment status
kubectl get all

# Access the service (local browser or curl)
minikube service nginx-service
curl $(minikube ip):30080
```

## 🔍 Verification
- Nginx welcome page served successfully
- Pod access via `kubectl logs` and `kubectl exec` works

## 🧹 Cleanup

```bash
kubectl delete -f .
```

## 🧩 Additional Notes
- Cluster: Minikube (Docker driver)
- OS: Ubuntu 24.04 (VMware)
