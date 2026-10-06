# TaskForge ⚒️ — Distributed Job Processing Platform (GitOps + Kubernetes)

Python microservices platform: a **FastAPI** gateway queues jobs in **Redis**, **background workers** process them,
and an **nginx** frontend shows live status. Deployed to Kubernetes through **Helm + Argo CD (GitOps)** with
queue-based autoscaling (**KEDA**) and full observability (**Prometheus + Grafana**).

**Stack:** Python · FastAPI · Redis · Docker · Docker Compose · Kubernetes · Helm · Argo CD · KEDA · Prometheus · Grafana · GitHub Actions · Trivy · Gitleaks · Ruff · pytest · Terraform · AWS

## Architecture
```
Browser → nginx frontend → FastAPI (api) → Redis queue → Python workers (scale 1..N)
                                │                              │
                           /metrics ─────────► Prometheus ◄── /metrics ──► Grafana

git push → GitHub Actions (ruff, pytest, helm lint, gitleaks, build, Trivy, push GHCR)
                          └─► Argo CD detects Git change → auto-syncs Helm chart to cluster
```

## Run locally (free)
```bash
make test                # unit tests
make up                  # http://localhost:8080  | Prometheus :9090 | Grafana :3000 (admin/admin)
```
Grafana → data source `http://prometheus:9090` → query `taskforge_queue_length`, `rate(taskforge_jobs_processed_total[1m])`.

## GitOps on free local Kubernetes (kind + Argo CD)
1. Replace `YOUR_USERNAME` in `helm/taskforge/values.yaml` and `argocd/application.yaml`; push to GitHub.
2. Wait for the Actions run, then make the 3 `taskforge-*` GHCR packages **public** (Packages → Settings → Visibility).
3. `./scripts/kind-setup.sh` (needs docker, kind, kubectl) — installs ingress, Argo CD and the app.
4. Add `127.0.0.1 taskforge.local` to `/etc/hosts` → open http://taskforge.local
5. Change `api.replicas` in `values.yaml`, push — Argo CD syncs automatically (that's GitOps!).

## Queue-based autoscaling (KEDA)
```bash
helm repo add kedacore https://kedacore.github.io/charts && helm install keda kedacore/keda -n keda --create-namespace
# set keda.enabled: true in values.yaml, push, then submit many "sleep" jobs and watch:
kubectl -n taskforge get pods -w
```

## Optional AWS (Terraform) — costs money if left running
`cd terraform && terraform init && terraform apply -var key_name=<keypair>` … `terraform destroy` when done.
