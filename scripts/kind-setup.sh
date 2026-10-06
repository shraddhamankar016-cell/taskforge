#!/usr/bin/env bash
# Free local Kubernetes + Ingress + Argo CD (needs: docker, kind, kubectl)
set -euo pipefail
cat <<KIND | kind create cluster --name taskforge --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - {containerPort: 80, hostPort: 80, protocol: TCP}
KIND
kubectl apply -f https://kind.sigs.k8s.io/examples/ingress/deploy-ingress-nginx.yaml
kubectl create namespace argocd
kubectl apply --server-side -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deploy/argocd-server --timeout=300s
kubectl apply -f argocd/application.yaml
echo "Argo CD password:"; kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
echo "UI: kubectl -n argocd port-forward svc/argocd-server 8443:443  -> https://localhost:8443 (user: admin)"
echo "App: add '127.0.0.1 taskforge.local' to /etc/hosts -> http://taskforge.local"
