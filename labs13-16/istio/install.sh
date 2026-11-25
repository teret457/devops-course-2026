#!/usr/bin/env bash
set -euo pipefail
: "${ISTIO_HOME:=$HOME/labs13-16/istio-1.32.0}"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
"$ISTIO_HOME/bin/istioctl" install -y --set profile=demo \
 --set components.egressGateways[0].name=istio-egressgateway \
 --set components.egressGateways[0].enabled=false \
 --set values.pilot.resources.requests.cpu=100m \
 --set values.pilot.resources.requests.memory=128Mi \
 --set values.global.proxy.resources.requests.cpu=10m \
 --set values.global.proxy.resources.requests.memory=32Mi \
 --set values.global.proxy.resources.limits.memory=128Mi
k3s kubectl create namespace lab15 --dry-run=client -o yaml | k3s kubectl apply -f -
k3s kubectl label namespace lab15 istio-injection=enabled --overwrite
k3s kubectl apply -n lab15 -f "$ISTIO_HOME/samples/bookinfo/platform/kube/bookinfo.yaml"
k3s kubectl apply -n lab15 -f "$ISTIO_HOME/samples/bookinfo/networking/bookinfo-gateway.yaml"
k3s kubectl apply -n lab15 -f "$ISTIO_HOME/samples/bookinfo/networking/destination-rule-all.yaml"
k3s kubectl apply -n lab15 -f "$ISTIO_HOME/samples/bookinfo/networking/virtual-service-all-v1.yaml"
k3s kubectl delete virtualservice productpage -n lab15 --ignore-not-found
k3s kubectl patch destinationrule ratings -n lab15 --type=json -p='[{"op":"replace","path":"/spec/subsets","value":[{"name":"v1","labels":{"version":"v1"}}]}]'
k3s kubectl apply -f "$(dirname "$0")/reviews-50-50.yaml"
k3s kubectl apply -f "$(dirname "$0")/strict-mtls.yaml"
k3s kubectl wait --for=condition=Available deployment --all -n lab15 --timeout=600s
"$ISTIO_HOME/bin/istioctl" analyze -n lab15
