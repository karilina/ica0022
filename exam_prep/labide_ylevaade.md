# Labide ülevaade (nädalad 2–8) — käsud, stsenaariumid, mis tuleb eksamil

★ = viga, mis sul labis PÄRISELT juhtus. Need on kõige väärtuslikumad — täpselt sellised tulevad Part B-s.

---

## Nädal 2 — Docker CLI alused

```
docker pull alpine:3.24
docker run --rm alpine echo ...          # ühekordne
docker run -it --rm alpine sh            # interaktiivne
docker run -d --name w2-sleep ...        # taustal
docker ps / docker ps -a                 # töötavad / kõik
docker logs <nimi>
docker inspect <nimi>                    # State.ExitCode, OOMKilled
docker exec -it <nimi> sh
docker top / docker stats --no-stream
docker run --memory=64m ...              # mälulimiit = cgroup
docker stop / docker rm
```
- `w2-fail`: `Exited (3)` → inspect ExitCode 3, logs näitab põhjust.
- Olematu käsk → Exit code 127, logs tühi, põhjus inspectis.

| Docker | Kubernetes |
|---|---|
| `docker ps -a` → Exited | `kubectl get pods` → CrashLoopBackOff |
| `docker logs` | `kubectl logs` / `--previous` |
| `docker inspect` | `kubectl describe pod` |
| `docker exec` | `kubectl exec` |
| `--memory` | `resources.limits.memory` |

---

## Nädal 3 — Dockerfile, build cache, multi-stage, registry

```
docker build -t ica0022:v0.1.0 .
docker run -d --name w3-basic -p 127.0.0.1:8080:8080 ica0022:v0.1.0
docker logs w3-app
docker exec w3-app id                   # uid=10001 → mitte root
docker history ica0022:v0.2.0           # kihid
docker tag ica0022:v1.0.0 karilina/ica0022:v1.0.0
docker push / docker image rm / docker pull
```
- ★ `waitress-server` (trükiviga) → `exec: "waitress-server": executable file not found in $PATH`. K8s-is sama tekst describe all.
- Build cache: muutsid app.py → ainult `COPY app.py` uuesti; muutsid requirements.txt → pip uuesti.
- Multi-stage: lõppimage'isse ainult venv + app.py.
- Sama tag, uus sisu → digest muutus. Tag on silt, digest on sisu → seepärast semantilised versioonid.

**Eksam:** Part A p1 (Dockerfile, 4p), p2 (push, 2p).

---

## Nädal 4 — Docker Compose

```
docker compose config / up / up -d / ps
docker compose logs --tail=10 app
docker compose exec app id
docker network inspect week4_backend
docker volume inspect week4_db-data
docker compose down        # volume jääb
docker compose down -v     # volume kustub
```
- init.sql jookseb AINULT kui andmekaust on tühi.
- `depends_on: service_healthy` + healthcheck ≈ K8s readiness probe.
- ★ App teises võrgus → `Name or service not known` (ei leia nime `db`). K8s-is sama viga = vale DB_HOST või Service.
- `down` + `up` → andmed alles (volume); `down -v` → kadunud.

---

## Nädal 5 — Kubernetes alused (Docker Desktop)

```
kubectl config current-context
kubectl get nodes / get namespaces / get pods -n kube-system
kubectl apply -f namespace.yaml
kubectl config set-context --current --namespace=ica0022
kubectl apply -f .
kubectl get all / get rs / get pods --show-labels / get pods -o wide
kubectl port-forward service/app 8080:8080
kubectl describe deployment app / describe service app
kubectl explain deployment.spec.replicas
kubectl scale deployment app --replicas=3
kubectl delete pod <pod>          # ReplicaSet teeb uue
kubectl get events --sort-by=.lastTimestamp
kubectl get endpointslices
kubectl run dns-test --rm -it --image=alpine:3.24 --restart=Never -- sh
```
1. Selector typo → endpointslices `<unset>` → Service ei leia podi.
2. Bad tag v9.9.9 → ErrImagePull/ImagePullBackOff. Vanad podid jäid tööle (RollingUpdate kaitseb).
3. Bad command `missing_module:app` → CrashLoopBackOff, Exit Code 1, logs: `No module named 'missing_module'`.
4. ★ DB pod kustutatud ilma PVC-ta → andmed kadusid → tabel puudu → app 503.
- DNS: `db` → `db.<namespace>.svc.cluster.local`.

**Eksam:** Part B tuum (image, traffic, crash).

---

## Nädal 6 — ConfigMap, Secret, PVC, probes

```
kubectl get storageclass
kubectl get configmap app-config -o yaml
kubectl get secret db-credentials -o yaml ; echo "..." | base64 -d
kubectl rollout status deployment/app
kubectl get pvc / get pv / describe pvc db-data
kubectl logs <db-pod>
kubectl describe pod <app-pod>     # Liveness / Readiness / Limits / Requests
```
- ★ `rollout status` jäi rippuma → uued podid katki (vale image).
- PVC `Pending` + `WaitForFirstConsumer` = NORMAALNE kuni pod tekib.
- ★ Postgres CrashLoopBackOff: `superuser password is not specified` → secret polnud külge pandud.
- DB pod kustutatud PVC-ga → visits alles.
- `Readiness probe failed: connection refused` kohe käivitumisel = normaalne.
- Broken: vale liveness → RESTARTS kasvab; vale readiness → 0/1; 64Gi → Pending FailedScheduling.

**Eksam:** Part A (ConfigMap/Secret, PVC 4p, probes 2p); Part B (node, probes, DB parool).

---

## Nädal 7 — EKS, ECR, Ingress

```
aws sso login --profile ica0022
aws sts get-caller-identity --profile ica0022
kubectl config use-context ica0022
kubectl auth can-i create deployments
kubectl describe resourcequota
kubectl get nodes ; kubectl get node <n> -o yaml
aws ecr get-login-password ... | docker login ...
docker buildx build --platform linux/amd64 -t <ECR>/students/kafina:v1.2.0 --push .
docker buildx imagetools inspect <ECR>/students/kafina:v1.2.0
kubectl get ingressclass
kubectl apply -f k8s/app-ingress.yaml ; kubectl describe ingress app ; kubectl get ingress
```
- ★ Vale context → "No resources found in default namespace".
- ★ Vale AWS profiil → vale konto.
- Quota: requests.cpu 1, requests.memory 2Gi, limits.memory 4Gi, pods 20, pvc 2, ingress 1, **loadbalancers 0** (ainult Ingress!).
- ★ `untolerated taint(s)` → system node'id ei võta podi; Karpenter tõi uue node'i.
- ★ PV seotud tsooniga (eu-north-1b) — EBS on tsoonipõhine.
- ★ Tag `1.2.0` vs `v1.2.0` → ErrImagePull not found.
- Ingress `target-type: ip` → ALB saadab otse podide IP-dele.

---

## Nädal 8 — Helm

```
helm registry login ...
helm pull oci://.../ica0022_postgresql --version 1.0.0 --untar --untardir prep
helm template .
helm dependency build
helm lint .
kubectl delete -f week_7/k8s/      # enne Helmi!
helm install app . --dry-run=server
helm install app .
helm upgrade app .                 # chart'i kaustast!
helm list / history / rollback
```
- ★ Dependency nimi `ica0022-postgresql` → not found; õige `ica0022_postgresql`.
- ★ db CreateContainerConfigError: Secret `db-credentials`, aga deployment otsis `db-auth` → `auth.existingSecret: db-credentials`.
- ★ app ErrImagePull: tag `1.2.0` → `v1.2.0`.
- ★ `helm upgrade` vales kaustas → `unable to detect chart`.

---

## Part B: incidendid ↔ sinu labid

| Incident | Kus nägid |
|---|---|
| Image issues (2) | N5 v9.9.9; ★ N7/N8 1.2.0 vs v1.2.0; N7 arm64 |
| Traffic not served (2) | N5 selector typo |
| Can't find a node (2) | N6 64Gi; ★ N7 taint |
| ??? kandidaadid | N5 bad command; N6 probes; ★ N6 postgres ilma paroolita; ★ N8 vale secreti nimi; N4 vale DB_HOST; N5 tabel puudu; N7 quota; N7 PVC/tsoon |

## Diagnostika algoritm
```
1. kubectl config current-context (+ namespace)
2. kubectl get pods / get all
3. kubectl describe pod <pod>         # Events, Last State, Exit Code
4. kubectl logs <pod> [--previous]
5. kubectl get endpointslices / describe svc
6. kubectl get events --sort-by=.lastTimestamp
7. kubectl get <ressurss> -o yaml
8. paranda → kubectl rollout status deploy/<d>
```
