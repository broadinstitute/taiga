#!/usr/bin/env bash
# Start all Taiga services for local development.
# Runs setup (Redis, MiniStack, DB) then launches mprocs.
# Usage: ./dev.sh
set -e
source setup_env.sh

# --- Redis ---
if redis-cli ping &>/dev/null; then
    echo "[ok] Redis already running"
else
    echo "[..] Starting Redis..."
    redis-server --daemonize yes
    echo "[ok] Redis started"
fi

# --- MiniStack (if settings.cfg is configured for it) ---
if grep -q "^S3_ENDPOINT_URL = 'http://localhost:4566'" settings.cfg 2>/dev/null; then
    if docker ps --format '{{.Names}}' | grep -q '^ministack$'; then
        echo "[ok] MiniStack already running"
    elif docker ps -a --format '{{.Names}}' | grep -q '^ministack$'; then
        echo "[..] Starting MiniStack..."
        docker start ministack >/dev/null
        echo "[ok] MiniStack started"
    else
        echo "[..] Starting MiniStack (first time — pulling image)..."
        docker run -d --name ministack -p 4566:4566 nahuelnucera/ministack >/dev/null
        sleep 3
        echo "[ok] MiniStack started"
    fi

    poetry run python -c "
import boto3
s3 = boto3.client('s3', endpoint_url='http://localhost:4566',
                  aws_access_key_id='test', aws_secret_access_key='test')
try:
    s3.head_bucket(Bucket='taiga-dev')
    print('[ok] taiga-dev S3 bucket exists')
except Exception:
    s3.create_bucket(Bucket='taiga-dev')
    print('[ok] Created taiga-dev S3 bucket')
" 2>/dev/null
fi

# --- Dev database ---
if [ ! -f instance/db.sqlite3 ]; then
    echo "[..] Creating dev database..."
    poetry run flask recreate-dev-db
    echo "[ok] Dev database created"
else
    echo "[ok] Dev database exists (instance/db.sqlite3)"
fi

exec mprocs --config mprocs.yaml
