#!/bin/sh

# setup kubectl

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client

# setup kind

[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.30.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# create kind cluster and configure kubectl to use it

kind create cluster
kubectl cluster-info --context kind-kind

# build docker images to push them to the cluster

docker build -t web:0.1.0 -f Dockerfile .
docker build -t celery:0.1.0 -f celery.dockerfile .
kind load docker-image web:0.1.0 celery:0.1.0

# create services and deployments

kubectl apply -f manifests/.

# port forward the web service

kubectl port-forward service/web 8000:8000