# ICA0022 — exam preparation

Exam: 180 min. **Part A** (30 p) — build the app from scratch. **Part B** (70 p) — 11 broken deployments in your namespace.
Allowed: only kubernetes.io/docs, docs.docker.com, helm.sh/docs. **Lab files are NOT allowed** → everything has to be in your head and in your fingers.

---

## Part B practice (13 incidents on Docker Desktop)

### Rules
- **Don't open `incidents/*.yaml`** — on the exam you won't have the files, only `kubectl get/describe/logs`. Apply them and pretend it's a black box.
- Don't open `SOLUTIONS.md` until you've tried yourself (at least 10–15 min per incident).
- Fix it "the way it was intended", not with workarounds (don't delete the deployment, don't swap the image for busybox).

### Setup (once)
```bash
# Docker Desktop → Settings → Kubernetes → Enable (cluster type kubeadm, so it can see local images)
kubectl config use-context docker-desktop

# build the app image locally (the week 7 code with /healthz and /readyz)
cd week_7/app
docker build -t ica0022:v1.2.0 .
cd ../..

kubectl apply -f exam_prep/base/
kubectl config set-context --current --namespace=exam-practice
kubectl rollout status deploy/db        # wait for the DB
kubectl apply -f exam_prep/incidents/
```
Start over: `kubectl delete ns exam-practice`, then `apply` both folders again.

### Tasks — what "fixed" means
| # | Done when |
|---|---|
| inc01 – inc11 | `kubectl get deploy incNN` shows `1/1`, RESTARTS don't grow over 2 minutes |
| inc02 | in addition: `kubectl exec -it debug -- wget -qO- http://inc02:8080/healthz` returns JSON |
| inc12-db, inc13-db | the postgres pod is `1/1 Running`, no restarts |

Check everything at once: `kubectl get deploy,pods,pvc` — all READY, no Pending/CrashLoop.

---

## Diagnostic algorithm (learn this by heart)

```
kubectl get deploy,rs,pods,svc,endpoints,pvc     # 1. overview: what's not READY?
kubectl describe pod <pod>                        # 2. Events at the bottom + State/Last State + Reason/Exit Code
kubectl logs <pod>  /  kubectl logs <pod> --previous   # 3. what the app said (--previous = before the restart)
kubectl get events --sort-by=.lastTimestamp       # 4. all events in the namespace
kubectl describe deploy <d>  /  kubectl describe rs -l app=<d>   # 5. NO pods at all? → look at the ReplicaSet
kubectl get deploy <d> -o yaml                    # 6. the full manifest (on the exam, this is your "file")
```

### Symptom → where to look → typical cause
| What you see | Where to look | Usually |
|---|---|---|
| `ErrImagePull` / `ImagePullBackOff` | describe pod → Events | wrong tag/repo, no access to the registry |
| `CrashLoopBackOff` | `logs --previous`, describe → Exit Code | app crashes: wrong command/args, missing env, no password |
| `RunContainerError` / `StartError` | describe → Message | `exec: ... not found`, `exec format error` (arm64 image on amd64) |
| `CreateContainerConfigError` | describe → Events | missing ConfigMap/Secret or a key in it; `runAsNonRoot` with a root image |
| `Pending` | describe pod → Events (FailedScheduling) | too large requests, nodeSelector/affinity/taints, unbound PVC |
| `Running 0/1` (not Ready) | describe → Readiness probe failed; logs | wrong readiness path/port, the app can't reach the DB |
| RESTARTS grow, Reason `OOMKilled`, code 137 | describe → Last State | memory limit too low |
| RESTARTS grow, "Liveness probe failed" | describe → Events | wrong liveness path/port, too small initialDelay |
| Deployment 0/1 and **no pods at all** | describe rs / get events → FailedCreate | ResourceQuota, missing resources, admission errors |
| Pod Ready, but the Service doesn't answer | `get endpoints`, `describe svc` | selector ≠ pod labels, wrong targetPort |
| PVC `Pending` | describe pvc | non-existent storageClass (note: on EKS `WaitForFirstConsumer` = Pending until a pod exists, that's normal) |
| Ingress has no ADDRESS / 502/503 | describe ingress, Events | ingressClassName, backend service/port, healthcheck path |

### How to fix
```bash
kubectl edit deploy <d>                          # edit the live manifest (a new rollout starts on save)
kubectl set image deploy/<d> app=<image:tag>
kubectl set resources deploy/<d> -c app --requests=cpu=50m,memory=64Mi --limits=memory=256Mi
kubectl get deploy <d> -o yaml > d.yaml  →  edit  →  kubectl apply -f d.yaml
kubectl rollout restart deploy/<d>               # !!! after changing a ConfigMap/Secret used as env — pods do NOT restart on their own
kubectl rollout status deploy/<d>
kubectl rollout undo deploy/<d>                  # roll back
kubectl create secret generic s --from-literal=KEY=val --dry-run=client -o yaml | kubectl apply -f -
kubectl get secret s -o jsonpath='{.data.KEY}' | base64 -d     # read a secret (Git Bash/WSL)
kubectl exec deploy/<d> -- env | grep DB_         # which env the container actually got
kubectl port-forward svc/<svc> 8080:8080          # test from your own machine: curl localhost:8080/healthz
```
Windows: `kubectl edit` opens Notepad. For VS Code: `$env:KUBE_EDITOR="code --wait"` (PowerShell).

---

## Part A practice — build everything from an empty folder

Do this **at least 2 times** in an empty folder, with a timer (goal: ≤ 90 min), with only the docs open.
Copy only `app.py` and `requirements.txt` from the week 7 code (on the exam you will be given the code or will need to have it).

**Checklist (points):**
1. **Dockerfile (4)** — `FROM ... AS builder` → venv + `pip install`; `FROM ... AS runtime` → `COPY --from=builder /opt/venv`, `COPY app.py`; `useradd` + `USER 10001`; `EXPOSE 8080`; `CMD waitress-serve --listen=0.0.0.0:8080 app:app`; `.dockerignore`
2. **Image (2)** — `docker buildx build --platform linux/amd64 -t <ECR>/students/<uniid>:v1.3.0 --push .` + `docker buildx imagetools inspect` (check linux/amd64)
3. **Manifests (8)** — Deployment, Service, ConfigMap (DB_HOST/PORT/NAME/USER), Secret (DB_PASSWORD) → `envFrom`
4. **Postgres + PVC (4)** — PVC, `subPath: pgdata`, `strategy: Recreate`, init.sql via ConfigMap → `/docker-entrypoint-initdb.d`
5. **Probes (2)** — liveness `/healthz` (doesn't touch the DB), readiness `/readyz` (checks the DB)
6. **Ingress (2)** — `ingressClassName: alb` + the annotations the teacher provides, backend = Service app:8080
7. **Helm (6)** — `helm create` → strip it down → templates for deployment/service/configmap/ingress, values; dependency on the teacher's postgres chart; `helm dependency build`, `helm lint`, `helm template`, `helm install`
8. **Questions (2)** — be ready to explain every line

**Templates without lab files:**
```bash
kubectl create deploy app --image=X --port=8080 --dry-run=client -o yaml
kubectl create svc clusterip app --tcp=8080:8080 --dry-run=client -o yaml
kubectl create cm app-config --from-literal=DB_HOST=db --from-literal=DB_PORT=5432 --dry-run=client -o yaml
kubectl create secret generic db-credentials --from-literal=DB_PASSWORD=x --dry-run=client -o yaml
kubectl create ingress app --class=alb --rule="/*=app:8080" --dry-run=client -o yaml
kubectl explain deployment.spec.template.spec.containers.readinessProbe
helm create mychart
```

**AWS / ECR / Helm commands:**
```bash
aws sso login --profile ica0022
aws eks update-kubeconfig --region eu-north-1 --name ica0022 --profile ica0022
kubectl config set-context --current --namespace=student-<uniid>
aws ecr get-login-password --region eu-north-1 --profile ica0022 | docker login --username AWS --password-stdin 609722444275.dkr.ecr.eu-north-1.amazonaws.com
aws ecr get-login-password --region eu-north-1 --profile ica0022 | helm registry login --username AWS --password-stdin 609722444275.dkr.ecr.eu-north-1.amazonaws.com
helm pull oci://609722444275.dkr.ecr.eu-north-1.amazonaws.com/charts/ica0022_postgresql --version 1.0.0 --untar
helm show values <chart>
```

### Part A traps (from your week 8 materials)
- **Moving from manifests to Helm:** Helm won't take over resources it didn't create ("invalid ownership metadata"). Your manifests create `db-data` (PVC) and `db-credentials`, and the teacher's chart with `fullnameOverride: db` creates **resources with the same names** (`db-data`, `db-credentials`, Service `db`). Before `helm install`, delete the manifest versions (`kubectl delete -f k8s/`).
- **In the teacher's chart:** the Secret is always created as `<fullname>-credentials`, but the postgres Deployment references `existingSecret` or `<fullname>-auth`. That's why `auth.existingSecret: db-credentials` was needed, otherwise postgres → CreateContainerConfigError. On the exam the chart may be different — **read its values.yaml and templates first**.
- **The password** in the chart's secret comes from `auth.password` (default `ica0022`), and the app reads `DB_PASSWORD` from the same secret — that's why they match.
- **initdb runs only on an empty data directory.** If the PVC already has data, the script won't run again.
- **`helm rollback` doesn't roll back data** on the PVC — only the manifests.
- **subPath: pgdata** — EBS has `lost+found`, and postgres won't initialize in a non-empty directory.
- **arm64 vs amd64:** on an M1/M2 Mac or ARM, without `--platform linux/amd64`, you'll get `exec format error` on EKS.

### Questions the teacher may ask (answer out loud)
1. Why multi-stage? What ends up in the final image, and what doesn't?
2. Why a non-root user? How do you check what the container runs as?
3. Difference between liveness and readiness? Why doesn't liveness check the DB?
4. What happens to traffic when readiness fails? And when liveness fails?
5. ConfigMap vs Secret — is a Secret encrypted? (base64 ≠ encryption)
6. How does the app find the DB? (Service DNS `db` → `db.<ns>.svc.cluster.local`)
7. port vs targetPort vs containerPort?
8. PVC / PV / StorageClass — who creates the disk?
9. Why `strategy: Recreate` for the DB? (RWO volume, Multi-Attach)
10. Why `subPath`?
11. What does `target-type: ip` do in the ALB annotation? Why `healthcheck-path: /readyz`?
12. What's `alias` and `condition` for in Chart.yaml dependencies? How do values get passed down to the subchart?
13. Why is `checksum/config` in the deployment template?
14. `helm template` vs `--dry-run=server` vs `helm lint`?
15. Why a semantic tag instead of `latest`?
