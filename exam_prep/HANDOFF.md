# ICA0022 — передача подготовки к экзамену (для нового чата)

> **Для Claude в новом чате:** это продолжение подготовки Kar к практическому экзамену по Docker/Kubernetes. Стиль, который работал: объяснения **на русском** (термины по-английски), Kar присылает вывод терминала, ты объясняешь, что в нём видно, и даёшь **следующий шаг / наводящий вопрос**, а не сразу ответ. Короткие шаги, таблицы «симптом → где смотреть». Хвалить конкретно, ошибки поправлять мягко. Kar работает в WSL (bash), редактор — vim.

---

## Экзамен
- **Четверг, 5 ноября 2026**, 180 минут. Разрешены только kubernetes.io/docs, docs.docker.com, helm.sh/docs. Файлы из лаб использовать **нельзя**.
- **Part A (30 б.)** — собрать приложение с нуля: multi-stage Dockerfile (4), push semver-тега linux/amd64 в ECR (2), Deployment+Service+ConfigMap+Secret (8), PostgreSQL с PVC через чарт учителя (4), probes (2), Ingress ALB (2), Helm chart + install (6), вопросы учителя (2).
- **Part B (70 б.)** — 11 сломанных деплойментов в своём namespace. Известные: image (2), traffic not served (2), can't find node (2), остальные «???». Чинить «как задумано», без обходных путей.
- Накануне учитель удалит всё в namespace и очистит ECR.

## Окружение Kar
- Repo: `~/ica0022` (GitHub `karilina/ica0022`), папки `week_3 … week_8`, `exam_prep/`.
- Локально: Docker Desktop Kubernetes (режим kind, узел `desktop-control-plane`), контекст `docker-desktop`. Локальные образы `ica0022:v1.1.0`, `ica0022:v1.2.0` есть.
- AWS: профиль `ica0022`, аккаунт `609722444275`, регион `eu-north-1`, контекст `ica0022`, namespace **`student-kafina`**, ECR-репозиторий **`students/kafina`** (там сейчас `v1.2.0`).
- Квота в `student-kafina`: requests.cpu 1, requests.memory 2Gi, limits.memory 4Gi, pods 20, pvc 2, ingress 1, **services.loadbalancers 0** (только Ingress).
- Команды входа:
  ```bash
  aws sso login --profile ica0022
  kubectl config use-context ica0022        # namespace student-kafina уже настроен
  aws ecr get-login-password --region eu-north-1 --profile ica0022 | docker login --username AWS --password-stdin 609722444275.dkr.ecr.eu-north-1.amazonaws.com
  aws ecr get-login-password --region eu-north-1 --profile ica0022 | helm registry login --username AWS --password-stdin 609722444275.dkr.ecr.eu-north-1.amazonaws.com
  ```

## Что уже пройдено (2–3 ноября)
- Разобраны логи лаб недель 2–8 → `exam_prep/labide_ylevaade.md`.
- Понятия: Deployment → ReplicaSet → Pod (хеш в имени пода = шаблон), Service (selector, port/targetPort, Endpoints), метки подов и узлов, контекст и namespace, ConfigMap/Secret (base64 ≠ шифрование), PVC/PV/StorageClass (WaitForFirstConsumer), liveness и readiness, requests/limits, command/args = ENTRYPOINT/CMD, waitress.
- **Week 5 broken:** selector typo, bad command, bad tag ✔. **Week 6 broken:** bad liveness, bad readiness, huge request ✔.
- **exam_prep (namespace `exam-practice`, вслепую):** inc01 image, inc02 targetPort, inc03 nodeSelector, inc04 ConfigMap name, inc05 args без command, inc06 liveness port, inc07 env перекрывает envFrom (DB_HOST), inc09 OOMKilled, inc10 quota exceeded, inc11 нет resources при quota, inc12-db secretKeyRef optional + неверный ключ ✔.
  - **inc08** пропущен, но разобран: неправильный пароль в `inc08-credentials` → исправить Secret + **`kubectl rollout restart`**.
  - **inc13-db** не доделан: PVC `inc13-data` с несуществующим StorageClass `premium-ssd` → scale 0, delete pvc, создать без storageClassName, scale 1.

## Слабые места: следить и напоминать
1. **Дважды редактировала под (`edit pod`) вместо деплоймента.** Правило: смотрю под, чиню владельца (`Controlled By` вверх до Deployment) или объект, на который под ссылается (svc/cm/secret/pvc).
2. Ходит по кругу (`describe deploy`, `edit deploy` без изменений), когда проблема в Service или PVC. Помогает вопрос: «на каком слое и в каком объекте ошибка?»
3. vim: удаляла `- args:` вместе с тире → `invalid`. Предлагать `kubectl set image/resources`, `kubectl patch`, `kubectl set selector`.
4. Не всегда проверяет результат после починки (новый хеш, `1/1`, RESTARTS не растут, `wget` через под `debug`).
5. Сначала путала метки узла и пода, `containerPort` и `targetPort`, старые ошибки в логах/Events и текущее состояние (смотреть Age).

## План на 4 ноября: Part A на EKS, один прогон с нуля (~2 ч)
Делать в пустой папке, по памяти, с открытой документацией. Порядок:
1. `aws sso login`, контекст `ica0022`, `kubectl get all` (пусто), `kubectl describe resourcequota`.
2. **Dockerfile** multi-stage по памяти (builder: venv + pip; runtime: `useradd 10001`, `COPY --from=builder /opt/venv`, `COPY app.py`, `ENV PATH`, `PYTHONUNBUFFERED=1`, `USER 10001:10001`, `EXPOSE 8080`, `CMD ["waitress-serve","--listen=0.0.0.0:8080","app:app"]`) + `.dockerignore`. Код: `week_7/app/app.py` + `requirements.txt`.
3. ECR login → `docker buildx build --platform linux/amd64 -t 609722444275.dkr.ecr.eu-north-1.amazonaws.com/students/kafina:v1.3.0 --push .` → `docker buildx imagetools inspect …` (linux/amd64).
4. Манифесты через `kubectl create … --dry-run=client -o yaml`: ConfigMap (DB_HOST=db, DB_PORT="5432", DB_NAME, DB_USER), Secret (DB_PASSWORD), Deployment (envFrom, probes `/healthz` и `/readyz`, resources), Service 8080.
5. PostgreSQL: проще сразу через Helm-чарт учителя (`helm pull oci://609722444275.dkr.ecr.eu-north-1.amazonaws.com/charts/ica0022_postgresql --version 1.0.0 --untar`). Сначала **прочитать его values.yaml и templates**.
6. Ingress: `ingressClassName: alb`, аннотации (`scheme: internet-facing`, `target-type: ip`, `healthcheck-path: /readyz`), backend app:8080 → `kubectl get ingress` (ADDRESS через пару минут).
7. Helm: `helm create` → оставить deployment/service/configmap/ingress + values; Chart.yaml dependency (`name: ica0022_postgresql` с подчёркиванием, `alias: postgresql`, `repository: oci://…/charts`); `helm dependency build`, `helm lint`, `helm template`, `helm install app . --dry-run=server`, `helm install app .`.
8. В конце `helm uninstall app` (учитель всё равно чистит).

### Ловушки Part A (уже встречались)
- Тег `1.2.0` vs `v1.2.0` → ErrImagePull.
- Без `--platform linux/amd64` → `exec format error` на EKS.
- **Helm не забирает чужие ресурсы**: удалить ресурсы, созданные манифестами (`kubectl delete -f …`), перед `helm install`. Чарт учителя с `fullnameOverride: db` создаёт `db`, `db-data`, `db-credentials`, `db-initdb`.
- В чарте учителя Secret создаётся как `<fullname>-credentials`, а Deployment postgres ищет `existingSecret` или `<fullname>-auth` → нужно `auth.existingSecret: db-credentials`, иначе CreateContainerConfigError (так было в week 8).
- Пароль в Secret чарта берётся из `auth.password` (по умолчанию `ica0022`), app берёт `DB_PASSWORD` из того же Secret.
- `subPath: pgdata` (на EBS есть lost+found). init.sql выполняется только на пустом диске.
- После изменения ConfigMap/Secret → `rollout restart` (в Helm это решает аннотация `checksum/config`).
- `helm upgrade` запускать из папки чарта.

## Утром 5 ноября (15 минут)
Перечитать алгоритм диагностики и таблицы в `exam_prep/README.md`. Открыть в браузере: kubectl Quick Reference, Configure Liveness/Readiness Probes, Ingress, ResourceQuota, Helm Chart Template Guide.

## Файлы
- `exam_prep/README.md`: алгоритм диагностики, таблицы (симптомы, коды probe, ошибки БД → переменная, Exit Code), чек-лист Part A, вопросы учителя.
- `exam_prep/SOLUTIONS.md`: решения inc01–13.
- `exam_prep/labide_ylevaade.md`: какие команды и сценарии были в каждой лабе.
- `exam_handover.md`: описание экзамена от учителя.
