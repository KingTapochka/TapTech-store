#!/bin/bash
set -euo pipefail

TAG="${1:-}"

# Принимаем только версии вида v1.2.3
if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Неверная версия: '$TAG'" >&2
  exit 1
fi

cd /home/devops/computer-store

echo "Деплой $TAG"
sed -i "s/^BACKEND_TAG=.*/BACKEND_TAG=${TAG}/" .env

docker compose pull backend
docker compose run --rm backend alembic upgrade head
docker compose up -d backend

# Ждём, пока backend станет healthy, максимум 60 секунд
for i in $(seq 1 12); do
  STATUS=$(docker inspect -f '{{.State.Health.Status}}' computer-store-backend-1)
  if [ "$STATUS" = "healthy" ]; then
    echo "Готово: $TAG работает"
    exit 0
  fi
  sleep 5
done

echo "Backend не стал healthy за 60 секунд" >&2
docker compose logs backend --tail 30 >&2
exit 1
