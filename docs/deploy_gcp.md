# Despliegue semanal en Google Cloud (Cloud Run Job + Cloud Scheduler)

El job ejecuta `python -m nba_pipeline`: Bronze incremental (10 días) → Silver → Gold, con parada inmediata ante cualquier fallo. Es idempotente: reejecutarlo es seguro.

Comandos en bash (Git Bash/WSL/Cloud Shell). Requiere `gcloud` y `docker` autenticados.

## 0. Variables

```bash
export PROJECT_ID="<tu-proyecto>"
export REGION="europe-west1"
export BUCKET="<tu-bucket-existente>"
export REPO="nba"
export JOB="nba-pipeline"
export TAG="$(git rev-parse --short HEAD)"   # tag inmutable; evita `latest`
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/nba-pipeline:${TAG}"
export JOB_SA="nba-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export SCHEDULER_SA="nba-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"
```

## 1. APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com
```

## 2. Artifact Registry

```bash
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker --location="$REGION" \
  --description="Imágenes del pipeline NBA"

gcloud auth configure-docker "${REGION}-docker.pkg.dev"
```

## 3. Construir y subir la imagen

```bash
docker build --platform linux/amd64 -t "$IMAGE" .
docker push "$IMAGE"
```

## 4. Service Accounts con privilegios mínimos

```bash
# Identidad con la que corre el job: solo objectAdmin sobre el bucket (no sobre el proyecto)
gcloud iam service-accounts create nba-pipeline-sa --display-name="NBA pipeline (Cloud Run Job)"
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${JOB_SA}" --role="roles/storage.objectAdmin"

# Identidad del scheduler: solo puede invocar este job
gcloud iam service-accounts create nba-scheduler-sa --display-name="NBA pipeline (Cloud Scheduler)"
```

## 5. Cloud Run Job

```bash
gcloud run jobs create "$JOB" \
  --image="$IMAGE" \
  --region="$REGION" \
  --service-account="$JOB_SA" \
  --memory=2Gi --cpu=1 \
  --task-timeout=3600s \
  --max-retries=1 \
  --tasks=1 \
  --set-env-vars="NBA_GCS_PROJECT=${PROJECT_ID},NBA_GCS_BUCKET=${BUCKET}"
```

- `2Gi` / `3600s` son valores de partida (pandas/pyarrow + reintentos y pausas hacia stats.nba.com). Ajustar tras la primera ejecución según uso real y duración.
- `--max-retries=1`: seguro porque Bronze acumula por `download_date`, Silver deduplica y Gold sobrescribe un objeto determinista.
- Opcionales: `NBA_USER_AGENT`, `NBA_PAUSE_SECONDS`, `NBA_PAUSE_JITTER_SECONDS` (se añaden a `--set-env-vars`).

Para desplegar una versión nueva:

```bash
gcloud run jobs update "$JOB" --region="$REGION" --image="$IMAGE"
```

## 6. Cloud Scheduler (lunes 08:00 UTC)

```bash
gcloud run jobs add-iam-policy-binding "$JOB" --region="$REGION" \
  --member="serviceAccount:${SCHEDULER_SA}" --role="roles/run.invoker"

gcloud scheduler jobs create http nba-pipeline-weekly \
  --location="$REGION" \
  --schedule="0 8 * * 1" --time-zone="UTC" \
  --http-method=POST \
  --uri="https://run.googleapis.com/v2/projects/${PROJECT_ID}/locations/${REGION}/jobs/${JOB}:run" \
  --oauth-service-account-email="$SCHEDULER_SA"
```

## 7. Verificación

### 7.1 Imagen en local (sin credenciales dentro de la imagen)

```bash
docker run --rm --entrypoint id "$IMAGE"                 # uid=10001, no root
docker run --rm --entrypoint ls "$IMAGE" -a /app         # sin .env ni .git

# Ejecución real contra un bucket de PRUEBAS, montando ADC solo en tiempo de ejecución
docker run --rm \
  -v "$HOME/.config/gcloud/application_default_credentials.json:/tmp/adc.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json \
  -e NBA_GCS_PROJECT="$PROJECT_ID" -e NBA_GCS_BUCKET="<bucket-de-pruebas>" \
  "$IMAGE" --days-back 3
```

(En Windows, la ruta del ADC es `%APPDATA%\gcloud\application_default_credentials.json`.)

### 7.2 Ejecución manual del job

```bash
gcloud run jobs execute "$JOB" --region="$REGION" --wait
gcloud run jobs executions list --job="$JOB" --region="$REGION" --limit=3
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=${JOB}" \
  --limit=50 --format="value(textPayload)"
```

### 7.3 Los 3 niveles se han actualizado

```bash
gcloud storage ls -l "gs://${BUCKET}/bronze_incremental/**" | tail -n 10
gcloud storage ls -l "gs://${BUCKET}/silver/**/data.parquet" | sort -k2 | tail -n 6
gcloud storage ls -l "gs://${BUCKET}/gold/matchup_features/**"
```

Comprobar que las fechas de modificación corresponden a la ejecución. Una segunda ejecución debe dejar los mismos objetos Silver/Gold con el mismo número de filas (idempotencia).

### 7.4 Disparo programado

```bash
gcloud scheduler jobs run nba-pipeline-weekly --location="$REGION"
```

## 8. Diagnóstico: stats.nba.com bloquea IPs de GCP

stats.nba.com suele bloquear o ralentizar rangos de IP de centros de datos. Que funcione en local no garantiza que funcione en Cloud Run.

**Síntomas:** la etapa `bronze` falla con timeouts, `403`/`429` o conexiones cortadas; la ejecución del job termina en error y no se llega a Silver/Gold (fail-fast).

**Cómo confirmarlo:**
1. Lanza solo el job y revisa los logs (7.2): busca líneas `FALLO <endpoint> <temporada>: ...`.
2. Compara con una ejecución local de `python -m nba_ingest --days-back 3` el mismo día: si local funciona y Cloud Run no, es bloqueo por IP.

**Mitigaciones, de menor a mayor esfuerzo:**
1. Subir pausas y reintentos: `gcloud run jobs update "$JOB" --region="$REGION" --update-env-vars=NBA_PAUSE_SECONDS=5,NBA_PAUSE_JITTER_SECONDS=3` y ampliar `--task-timeout`.
2. Fijar el `NBA_USER_AGENT` a uno de navegador actual.
3. Salida con IP estática: VPC + Cloud NAT con IP reservada (`--network`, `--subnet`, `--vpc-egress=all-traffic` en el job). Una IP estable permite además comprobar si está en lista negra.
4. Ejecutar solo Bronze desde fuera de GCP (otra máquina/proveedor) y dejar Silver/Gold en Cloud Run, que no dependen de la API.
