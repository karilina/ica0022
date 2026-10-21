```bash
# 1 lab prep
# Install helm
# https://helm.sh/docs/intro/install

# This should return helm version v4.x.x
helm version

aws sso login --profile ica0022
aws ecr get-login-password --region eu-north-1 --profile ica0022 | helm registry login --username AWS --password-stdin 609722444275.dkr.ecr.eu-north-1.amazonaws.com

helm pull oci://609722444275.dkr.ecr.eu-north-1.amazonaws.com/charts/ica0022_postgresql --version 1.0.0 --untar --untardir prep

# This is all for the prep, the following commands will be run during the lab

# 2 Building the Helm chart
## Inside the helm folder
helm dependency build
helm lint .
helm template app .

# To see what will be built
helm install app . --dry-run=server

# Install, upgrade and rollback the helm chart
helm install app .
helm upgrade app .
helm rollback app <version>

# 3 View Helm resources
helm list
helm history app

# 4 Introduce bugs
helm upgrade app . --set-string image.tag=9.9.9
helm upgrade app . --set probes.readinessPath=/ready --wait --timeout 90s

# 5 Cleanup
helm uninstall app
```
