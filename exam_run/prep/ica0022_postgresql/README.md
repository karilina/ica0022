# ica0022_postgresql

PostgreSQL 17 chart for the ICA0022 course application. It runs a single PostgreSQL Pod and creates:

| Object | Name |
|--------|------|
| Deployment | `<fullname>` |
| Service (ClusterIP) | `<fullname>` |
| Secret | `<fullname>-credentials` |
| PersistentVolumeClaim | `<fullname>-data` |
| ConfigMap (only when `initdb.scripts` is set) | `<fullname>-initdb` |

`<fullname>` is `fullnameOverride`, or the release name if that is empty.

## Values

### Must be set

| Key | Example | What it does |
|-----|---------|--------------|
| `enabled` | `true` | Parent chart only. Read by `condition: postgresql.enabled`; `false` leaves the database out of the release. |
| `fullnameOverride` | `db` | Name of every object. Your app connects to the Service by this name, so it must match `DB_HOST` in the app config. |
| `auth.database` | `ica0022` | Database created on first start (`POSTGRES_DB`). Must match the app's `DB_NAME`. |
| `auth.username` | `ica0022` | Database user created on first start (`POSTGRES_USER`). Must match the app's `DB_USER`. |
| `auth.password` | `ica0022` | Password for that user. Stored in the `<fullname>-credentials` Secret. |
| `resources.requests.cpu` | `100m` | CPU request for the PostgreSQL container. |
| `resources.requests.memory` | `256Mi` | Memory request for the PostgreSQL container. |
| `resources.limits.memory` | `512Mi` | Memory limit for the PostgreSQL container. |

### Optional (defaults work)

| Key | Default | What it does |
|-----|---------|--------------|
| `image.repository` | `postgres` | PostgreSQL image. |
| `image.tag` | `17-bookworm` | Image tag. Keep major version 17; an existing data directory will not start under another major version. |
| `image.pullPolicy` | `IfNotPresent` | Image pull policy. |
| `persistence.size` | `1Gi` | Size of the PVC. |
| `persistence.storageClass` | `""` | StorageClass for the PVC. Empty means the cluster default. |
| `persistence.subPath` | `pgdata` | Subdirectory on the volume where PostgreSQL keeps its data. |
| `initdb.enabled` | `true` | Whether `initdb.scripts` are mounted at all. |
| `initdb.scripts` | `{}` | Map of file name to SQL. Each entry becomes a file in `/docker-entrypoint-initdb.d`. Scripts run only the first time, when the data directory is empty. They do not run again on upgrade or restart. |
| `service.port` | `5432` | Service port. Must match the app's `DB_PORT`. |

`auth.secretKey` is only printed in the install notes. The key names inside the Secret are fixed.

## Connecting your application

The chart creates Secret `<fullname>-credentials` with two keys that hold the same password:

| Key | Used by |
|-----|---------|
| `POSTGRES_PASSWORD` | PostgreSQL container |
| `DB_PASSWORD` | Your application |

Point your app at that Secret (with `fullnameOverride: db`, it is `db-credentials`). Keep the app's connection settings in line with the database values:

| App value | Must equal |
|-----------|-----------|
| `DB_HOST` | `postgresql.fullnameOverride` |
| `DB_PORT` | `postgresql.service.port` |
| `DB_NAME` | `postgresql.auth.database` |
| `DB_USER` | `postgresql.auth.username` |
| Secret name | `<postgresql.fullnameOverride>-credentials` |

## Provided initdb

```yaml
postgresql:
  initdb:
    scripts:
      init.sql: |
        CREATE TABLE IF NOT EXISTS counter (
            id integer PRIMARY KEY CHECK (id = 1),
            visits bigint NOT NULL DEFAULT 0
        );

        INSERT INTO counter (id, visits)
        VALUES (1, 0)
        ON CONFLICT (id) DO NOTHING;
```

## Things to know

- There is always exactly one replica. The Deployment uses `Recreate`, so an upgrade stops the old Pod before it starts the new one, and the database is down for a short time.
- Changing `auth.*` after the first install does not change the existing database user or password; PostgreSQL only reads them when it initialises an empty data directory.
- `helm rollback` restores the manifests, not the data on the volume.
- To read the default values from the published chart:

```bash
helm show values oci://609722444275.dkr.ecr.eu-north-1.amazonaws.com/charts/ica0022_postgresql --version 1.3.0
```
