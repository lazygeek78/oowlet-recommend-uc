# oowlet-recommend-uc. Build from the repository root (needs proto/):
#   docker build -f oowlet-recommend-uc/Dockerfile -t recommend-uc .
FROM python:3.12-slim AS build
WORKDIR /app
COPY oowlet-recommend-uc/requirements.txt oowlet-recommend-uc/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY proto/recommenduc /proto/recommenduc
COPY proto/eventlayer /proto/eventlayer
COPY proto/feature_service /proto/feature_service
COPY oowlet-recommend-uc/ ./
RUN python scripts/gen_protos.py /proto && python scripts/import_check.py && python -m pytest -q

FROM python:3.12-slim
ARG VERSION=dev
ARG COMMIT=unknown
LABEL com.oowlet.service=recommend-uc com.oowlet.version=$VERSION com.oowlet.commit=$COMMIT
RUN useradd --system --uid 10071 --home /app ruc
WORKDIR /app
COPY --from=build /app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=build /app/ruc ./ruc
COPY --from=build /app/oowlet ./oowlet
USER ruc
EXPOSE 50070
# configuration: RUC_* environment variables; secrets mounted as files (see .env.example)
ENTRYPOINT ["python", "-m", "ruc.cli", "serve"]
