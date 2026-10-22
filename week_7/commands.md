```bash
# 1  preflight
aws --version
docker buildx version
kubectl config current-context

# 2  AWS access
aws sso login --profile ica0022
aws sts get-caller-identity --profile ica0022

# 3  cluster
aws eks update-kubeconfig --region eu-north-1 --name ica0022 --profile ica0022
kubectl config set-context --current --namespace=student-<uniid>
kubectl auth can-i --list
kubectl get roles                                  # Forbidden, on purpose
kubectl describe resourcequota

# 4  database
kubectl apply -f k8s/app-config.yaml
kubectl apply -f k8s/db-credentials.yaml
kubectl apply -f k8s/db-init.yaml
kubectl apply -f k8s/db-pvc.yaml
kubectl describe pvc db-data
kubectl apply -f k8s/db-deployment.yaml
kubectl apply -f k8s/db-service.yaml
kubectl get events --sort-by=.lastTimestamp
kubectl exec deploy/db -- ls -la /var/lib/postgresql/data

# 5  build, push, deploy
aws ecr get-login-password --region eu-north-1 --profile ica0022 | docker login --username AWS --password-stdin 609722444275.dkr.ecr.eu-north-1.amazonaws.com
docker buildx build --platform linux/amd64 -t 609722444275.dkr.ecr.eu-north-1.amazonaws.com/students/uniid:v1.2.0 --push .      # run from app/
docker buildx imagetools inspect 609722444275.dkr.ecr.eu-north-1.amazonaws.com/students/uniid:v1.2.0
kubectl apply -f k8s/app-deployment.yaml
kubectl apply -f k8s/app-service.yaml
kubectl rollout status deployment/app
kubectl get pods -o wide

# 6  ingress
kubectl apply -f k8s/app-ingress.yaml
kubectl describe ingress app
kubectl get ingress -w

# 7  cleanup
kubectl delete -f k8s/app-ingress.yaml
------------------------------------------
kubectl get deploy
kubectl vim (edit) deploy app
(replicas 0)
kubectl vim (edit) deploy db
(replicas 0)
kubectl get pods

```
