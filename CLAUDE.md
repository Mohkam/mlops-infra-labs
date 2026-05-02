## Repository Overview

This monorepo contains MLOps infrastructure learning labs plus three production-grade platforms.

Contents (high-level):

```
mlops-infra-labs/
├── mlops-platform/                  # Base platform (Airflow + MLflow + FastAPI)
├── mlops-platform-triton/           # + Triton Inference Server
├── mlops-platform-feature-store/    # + Feast + Redis + Triton
├── airflow/                         # Airflow tutorials (5 labs)
├── k8s-basic/                       # Kubernetes basics (5 labs)
├── mlflow/                          # MLflow tracking tutorial
├── airflow_mlflow_fastapi_dockerCompose/  # Docker Compose integration example
├── airflow_mlflow_fastapi_helm/     # Helm integration example
└── terraform/                       # Terraform IaC examples
```

## Platform Architecture (common for all three platforms)

All platforms follow the same directory layout:

```
<platform>*/
├── apps/           # ArgoCD Application manifests
├── bootstrap/      # ArgoCD + MetalLB bootstrap scripts
├── charts/         # Helm charts (airflow, fastapi, mlflow, [triton], [feast])
│   └── <chart>/
│       ├── Chart.yaml
│       ├── image/          # Dockerfile + requirements.txt
│       ├── templates/      # Kubernetes resource templates
│       └── values/
│           ├── base.yaml   # common settings
│           ├── dev.yaml    # dev overrides
│           └── prod.yaml   # prod overrides
├── envs/
│   ├── dev/
│   │   ├── certificates/   # cert-manager TLS
│   │   ├── monitoring/     # ServiceMonitor, AlertRules
│   │   ├── observability/  # Loki/Promtail values
│   │   └── sealed-secrets/ # encrypted secrets
│   └── prod/               # same structure for prod
└── ops/
    ├── storage/        # NFS PV/PVC definitions (Retain policy)
    └── seal/           # SealedSecret re-encryption scripts
```

## Notes
- English terms such as `Airflow`, `MLflow`, `FastAPI`, `Helm`, `ArgoCD` are kept as-is.Non-English terms are translated to English while preserving existing English content.