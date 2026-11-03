# SOLUTIONS — open only after you've tried yourself!

---

### inc01 — Image issue ★
- **Symptom:** `ErrImagePull` → `ImagePullBackOff`.
- **Where:** `describe pod` → Events: `Failed to pull image "ica0022:1.2.0" ... not found`.
- **Cause:** the tag is `1.2.0` instead of `v1.2.0`. Check which tags exist: `docker images` (on EKS: `aws ecr describe-images`).
- **Fix:** `kubectl set image deploy/inc01 app=ica0022:v1.2.0`

### inc02 — Traffic not reaching the pod ★
- **Symptom:** the pod is `1/1 Ready`, but `wget http://inc02:8080` → `connection refused`.
- **Where:** `kubectl get endpoints inc02` → `10.1.x.x:8000` — the port is visible right there! `describe svc inc02` → TargetPort 8000.
- **Cause:** Service `targetPort: 8000`, while the app listens on 8080.
- **Fix:** `kubectl edit svc inc02` → `targetPort: 8080`.
- **Lesson:** if endpoints are **empty**, the selector doesn't match the labels (week 5 typo). If endpoints exist but the connection fails, it's the wrong targetPort.

### inc03 — Can't find a node ★
- **Symptom:** `Pending`.
- **Where:** `describe pod` → `FailedScheduling: 0/1 nodes are available: 1 node(s) didn't match Pod's node affinity/selector`.
- **Cause:** `nodeSelector: node-type: gpu` — no node has that label (`kubectl get nodes --show-labels`).
- **Fix:** `kubectl edit deploy inc03` → remove `nodeSelector`. (You can't label nodes — you only have rights in your namespace.)
- Other causes of the same category: huge requests (week 6 `64Gi`), affinity, taints without tolerations.

### inc04 — Missing ConfigMap ★★
- **Symptom:** `CreateContainerConfigError`.
- **Where:** `describe pod` → `Error: configmap "app-configuration" not found`. `kubectl get cm` → there's `app-config`.
- **Fix:** in the deployment `configMapRef.name: app-config`.

### inc05 — args instead of command ★★★
- **Symptom:** `RunContainerError`/`CrashLoopBackOff`, logs are empty.
- **Where:** `describe pod` → `exec: "--listen=0.0.0.0:8080": executable file not found in $PATH`.
- **Cause:** in Kubernetes `command` = Docker `ENTRYPOINT`, `args` = Docker `CMD`. The image has no ENTRYPOINT, only `CMD ["waitress-serve", ...]`. `args` replaced the CMD → the container tries to run `--listen=...` as a program.
- **Fix:** remove `args` (the image's CMD is already correct) or replace it with `command: ["waitress-serve", "--listen=0.0.0.0:8080", "app:app"]`.

### inc06 — Liveness on the wrong port ★★★
- **Symptom:** the pod is periodically Ready, but RESTARTS keep growing.
- **Where:** `describe pod` → `Liveness probe failed: ... :8081/healthz: connect: connection refused` + `Container app failed liveness probe, will be restarted`.
- **Fix:** `livenessProbe.httpGet.port: 8080`.

### inc07 — env overrides envFrom ★★★★
- **Symptom:** `Running 0/1`, no restarts.
- **Where:** `describe` → `Readiness probe failed: HTTP probe failed with statuscode: 503`. `kubectl logs` → `Readiness check failed: ... failed to resolve host 'database'`. `kubectl exec deploy/inc07 -- env | grep DB_HOST` → `database`.
- **Cause:** the ConfigMap has `DB_HOST=db`, but there's also `env: DB_HOST=database` in the deployment. **`env` takes priority over `envFrom`.**
- **Fix:** remove that `env` block from the deployment.

### inc08 — Wrong password in the Secret ★★★★
- **Symptom:** `Running 0/1`.
- **Where:** logs → `password authentication failed for user "ica0022"`. The deployment uses `secretRef: inc08-credentials`. `kubectl get secret inc08-credentials -o jsonpath='{.data.DB_PASSWORD}' | base64 -d` → `ica0022-password`, but the DB has `ica0022-pass` (compare with `db-credentials`).
- **Fix:**
  ```bash
  kubectl create secret generic inc08-credentials --from-literal=DB_PASSWORD=ica0022-pass --dry-run=client -o yaml | kubectl apply -f -
  kubectl rollout restart deploy/inc08     # without this the pod keeps the old env!
  ```
- **Lesson:** env from a Secret/ConfigMap is read **only when the container starts**.

### inc09 — OOMKilled ★★★
- **Symptom:** `CrashLoopBackOff`, restarts.
- **Where:** `describe pod` → `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` (sometimes `StartError ... container init was OOM-killed`).
- **Cause:** `limits.memory: 16Mi` — Python + psycopg doesn't fit.
- **Fix:** `kubectl set resources deploy/inc09 -c app --requests=cpu=50m,memory=64Mi --limits=memory=256Mi`

### inc10 — ResourceQuota exceeded ★★★★★
- **Symptom:** `inc10 0/1`, and `kubectl get pods -l app=inc10` shows **nothing** (not even Pending!).
- **Where:** `kubectl describe deploy inc10` → `ReplicaFailure True FailedCreate`; `kubectl describe rs -l app=inc10` / `get events` → `exceeded quota: practice-quota, requested: requests.memory=3Gi, used: ..., limited: requests.memory=2Gi`. `kubectl describe resourcequota`.
- **Fix:** sensible resources: requests 64Mi, limits 256Mi.
- **Lesson:** Pending = the scheduler can't find a node. No pods at all = the API server (admission/quota) rejected creating the pod → look at the ReplicaSet.

### inc11 — No resources with a quota in place ★★★★★
- **Symptom:** same as inc10: no pods.
- **Where:** events on the RS → `failed quota: practice-quota: must specify limits.memory for: app; requests.cpu for: app; requests.memory for: app`.
- **Cause:** if a quota limits `requests.*`/`limits.*`, every pod must declare them.
- **Fix:** add a `resources` block (requests cpu/memory + limits memory).

### inc12-db — Postgres without a password ★★★★★
- **Symptom:** `CrashLoopBackOff`.
- **Where:** `kubectl logs deploy/inc12-db` → `Error: Database is uninitialized and superuser password is not specified.`
- **Cause:** `secretKeyRef.key: POSTGRES_PASSWORD` with `optional: true`, but the secret `inc12-db-auth` has the key `POSTGRES_PASSWD` (`kubectl describe secret inc12-db-auth` shows the keys). Because of `optional`, Kubernetes didn't throw an error — it just didn't set the variable.
- **Fix:** bring the key back to `POSTGRES_PASSWORD` in the secret (or change the key in the deployment), then `kubectl rollout restart deploy/inc12-db`.

### inc13-db — PVC with a non-existent StorageClass ★★★★★★
- **Symptom:** the postgres pod is `Pending`, PVC `Pending`.
- **Where:** `describe pod` → `pod has unbound immediate PersistentVolumeClaims`; `describe pvc inc13-data` → `storageclass.storage.k8s.io "premium-ssd" not found`; `kubectl get storageclass` → `hostpath (default)` (on EKS: gp2/gp3).
- **Cause:** a PVC's `storageClassName` **can't be changed** (immutable) — you have to recreate it.
- **Fix:**
  ```bash
  kubectl get pvc inc13-data -o yaml > pvc.yaml
  # in pvc.yaml: storageClassName: hostpath (or remove the line → default); delete status, uid, resourceVersion, creationTimestamp, annotations
  kubectl scale deploy inc13-db --replicas=0
  kubectl delete pvc inc13-data
  kubectl apply -f pvc.yaml
  kubectl scale deploy inc13-db --replicas=1
  ```

---

## What else could come up on the exam (EKS, not reproducible on Docker Desktop)
- **`exec format error`** — the image was built for arm64 (week 7 broken: tag `v1.2.1-arm64`). Fix: an amd64 tag.
- **Multi-Attach error for volume** — the DB Deployment with `RollingUpdate` and an RWO EBS volume: the new pod can't attach the disk while the old one holds it. Fix: `strategy: type: Recreate`.
- **postgres: `directory ... exists but is not empty`** — no `subPath`, the EBS disk has `lost+found`.
- **Ingress without an address / 503** — wrong `ingressClassName`, backend service/port, or the ALB healthcheck hits a path that returns ≠200.
- **`targetPort: http`** while the container port has no `name: http` → endpoints exist but have no port.
- **`runAsNonRoot: true`** with an image that runs as root → `CreateContainerConfigError: container has runAsNonRoot and image will run as root`.
- **readOnlyRootFilesystem** → the app/postgres can't write → crash, look in the logs.
- **initContainer** waiting for `db` under the wrong name → `Init:0/1` forever → `kubectl logs <pod> -c <init-name>`.
- **CPU limit too low** → the app is slow, probes hit their timeout → restarts.
- **NetworkPolicy** blocks traffic to the DB → readiness 503, `kubectl get networkpolicy`.
- **imagePullPolicy: Never/Always** with a local/missing image.
