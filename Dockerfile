FROM python:3.12-slim

ARG TARGETARCH

ENV TZ=Asia/Ho_Chi_Minh

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SUPERCRONIC_VERSION=v0.2.34

WORKDIR /app

# 安装运行时依赖与 supercronic（用于定时任务）
RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates bash tzdata && \
    ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && echo ${TZ} > /etc/timezone && \
    case "${TARGETARCH}" in \
      amd64) \
        export SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64; \
        export SUPERCRONIC_SHA1SUM=e8631edc1775000d119b70fd40339a7238eece14; \
        ;; \
      arm64) \
        export SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-arm64; \
        export SUPERCRONIC_SHA1SUM=4ab6343b52bf9da592e8b4bb7ae6eb5a8e21b71e; \
        ;; \
      *) \
        echo "Unsupported TARGETARCH=${TARGETARCH}"; \
        exit 1; \
        ;; \
    esac && \
    for i in 1 2 3 4 5; do \
      echo "Downloading supercronic attempt ${i}/5"; \
      if curl --fail --silent --show-error --location --retry 3 --retry-delay 2 --connect-timeout 30 --max-time 120 -o supercronic "${SUPERCRONIC_URL}"; then \
        echo "Download successful"; \
        break; \
      fi; \
      if [ "$i" -eq 5 ]; then \
        echo "Failed to download supercronic"; \
        exit 1; \
      fi; \
      sleep $((i * 2)); \
    done && \
    echo "${SUPERCRONIC_SHA1SUM}  supercronic" | sha1sum -c - && \
    chmod +x supercronic && mv supercronic /usr/local/bin/supercronic && \
    supercronic -version && \
    apt-get remove -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 拷贝源码
COPY . .

# 统一入口脚本（cron + SSE server）
RUN cp docker/entrypoint.sh /entrypoint.sh && \
    sed -i 's/\r$//' /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    cp docker/manage.py /app/manage.py && \
    chmod +x /app/manage.py && \
    mkdir -p /app/config /app/output

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
