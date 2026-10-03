# TatpTech Store

Учебный DevOps-проект: инфраструктура интернет-магазина клавиатур на собственном VPS.
Приложение минимальное, основная работа в инфраструктуре вокруг него.

Сайт: https://tatptech24.ru

## Стек

- Backend: FastAPI, PostgreSQL 16, Redis 7
- Docker Compose, Nginx (reverse proxy, HTTPS через Let's Encrypt)
- Миграции схемы: Alembic
- Тесты: pytest
- Сервер: Ubuntu 24.04, UFW, SSH только по ключу, автообновления безопасности

## Схема

    интернет → nginx :443 → backend :8000 → postgres, redis

## Что сделано

- Секреты вынесены в .env, в репозитории только .env.example
- Внутренние сервисы не публикуют порты наружу
- Healthcheck у всех сервисов, nginx не падает при недоступности backend
- HTTPS с автопродлением сертификата
- Миграции Alembic вместо ручного SQL
- Журнал инцидентов: docs/incidents.md

## Запуск

    cp .env.example .env    # заполнить значения
    docker compose up -d
    docker compose run --rm backend alembic upgrade head

## В планах

- Фронтенд: каталог, корзина, оформление заказа; сборка multi-stage Docker
- GitLab CI/CD
- Ansible
- Бэкапы PostgreSQL
- Мониторинг Prometheus и Grafana
- Kubernetes (k3s)
