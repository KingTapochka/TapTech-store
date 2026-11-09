##1 PostgreSQL на хосте не принимет подключения из контейнера

Симптом: 
Сначала "connection to server at 172.17.0.1, port 5432 failed: Connection refused"
Потом "FATAL: no pg_hba.conf entry for host "172.17.0.2", user "<user>", database "<db>", no encryption"

Диагностика
1. Проверил через ss -lntp какие порты слушает postgreSQL, он слушает 127.0.0.1, а адреса 172.17.0.1 в списке нет
2. Добавил адрес в listen_addresses, перезапустил. Далее ошибка сменилась на no pg_hba.conf entry. Есть соединение, но не нет разрешения

Исправление
1. listen_adresses = 'localhost,172.17.0.1'
2. В pg_hba.conf добавил правило host shop db shop user 172.17.0.0/16 scram-sha-256
3. Перезапуск PostgreSQL


##2 Redis отклоняет команды из контейнера

Симптом:
backend падает при старте c ошибкой "DENIED Redis is running in protected mode"

Диагностика:

1. ss -lntp, Redis сдушает 127.0.0.1 и 172.17.0.1 проблем с сетью нет
2. Ошибка DENIED означает соединение устанавливается, но Redis отклоняет команды, потому что работает в protect mode

Исправление: задал пароль через requirepass, теперь строка в формате redis://:<пароль>@<хост>:6379/0


## 3 Порт backend открыт в интернет, хотя UFW его запрещает

Симптом: 
В логах backend кто то отправляет запросы на порт 8000. UFW разрешает только 22, 80, 443

Диагностика: 
1. ufw status: порта 8000 в разрешенных нет
2. Проверил, через внешний сервис ip и порт, он открыт
3. docker ps: у backend опубликован 8000 порт
4. В iptables Docker добавил свои правила перенаправления на контейнер

Исправление:
Убрал публикацию порта у backend в docker-compose. Доступ к backend будет только через nginx 
внутри docker-compose сети. Правила UFW не защищают порты опубликованные docker

## 4 Nginx не находит backend после ошибки с портом 80

Симптом:
Nginx постоянно перезапускается, статус "Restarting". В логах:
"host not found in upstream backend in /etc/nginx/conf.d/default.conf:6"
Backend при этом работает.

Диагностика:
1. При первом запуске nginx упал с ошибкой "failed to bind host port 0.0.0.0:80/tcp: address already in use".
2. Через sudo ss -lntp | grep ':80 ' нашёл, что порт 80 на хосте занят nginx, остановил и отключил автозапуск.
3. Повторный docker compose up -d не пересоздал nginx, а запустил тот же контейнер. Видно по id.
4. По логам entrypoint проходит "Configuration complete", падает сам nginx: При чтении proxy_pass не может найти 
   адрес backend.

Исправление:
1. docker compose up -d --force-recreate nginx, контейнер создан заново с новым ID.
2. Проверил через docker network inspect computer-store_default, что все 4 контейнера в одной сети.
3. curl http://localhost/api/health возвращает ответ от backend.

## 5 Редирект с HTTPS на HTTP и 502 после правки nginx

Симптом:
1. curl -i https://tatptech24.ru/api/products возвращает 307 с location: http, а не https.
2. После добавления resolver в конфиг nginx все запросы стали получать 502.

Диагностика:
1. docker inspect: у uvicorn есть --proxy-headers, команда применилась.
2. Отправил запрос в backend напрямую из контейнера nginx через wget с заголовком X-Forwarded-Proto: 
   https. Backend ответил редиректом на https,значит проблема в nginx.
3. Конфиг внутри контейнера отличался от файла на диске:
   файл смонтирован по отдельности, после правки контейнер видел старую версию.
4. 502: в proxy_pass переменная $upstream, а строки resolver не было.
   Без resolver nginx не может найти адрес backend при запросе.

Исправление:
1. Добавил resolver 127.0.0.11 valid=10s в блок server.
2. Перенёс конфиг в nginx/conf.d и монтирую папку, а не файл. Теперь достаточно nginx -s reload.

## 6  Сборка образа в CI не подключается к Docker

Симптом:
Задача build: "Cannot connect to the Docker daemon at tcp://docker:2375".

Диагностика:
1. dind слушает только порт 2376 с TLS (DOCKER_TLS_CERTDIR задан).
2. Клиент не нашёл сертификаты: dind и задача в разных контейнерах,
   папка /certs у каждого своя. Клиент откатился на 2375 без TLS.

Исправление:
В /etc/gitlab-runner/config.toml добавил volumes = ["/certs/client", "/cache"],
перезапустил Runner.

## 7 Ключ деплоя не читается в CI

Симптом:
Задача deploy: "Load key: error in libcrypto", затем "Permission denied (publickey)".

Диагностика:
1. Ключ хранился как многострочная переменная типа File.
2. При вставке в GitLab формат ключа испортился.
3. После перехода на base64 ssh-keygen -l показал "is not a key file"
   строка обрезалась при копировании из терминала.

Исправление:
1. Ключ закодировал в одну строку base64 -w0, в CI раскодирую через base64 -d.
2. Файл перенёс на компьютер через scp и скопировал из блокнота.
3. В задачу добавил ssh-keygen -l: отпечаток в CI совпал с отпечатком на сервере.
4. Ключ ограничен в authorized_keys через command= и restrict.

## 8 Деплой backend пересоздаёт базу и Redis

Симптом:
В логе деплоя "Container computer-store-postgres-1 Recreate" и то же у redis,
хотя менялся только backend.

Диагностика:
docker compose run и up по умолчанию проверяют и поднимают зависимости сервиса
и пересоздают их, если конфигурация отличается от запущенных контейнеров.

Исправление:
В deploy.sh добавил --no-deps к run и up. Проверил откатом через GitLab Environments:
postgres и redis больше не пересоздаются.

## 9 Postgres и Redis пересоздаются без изменений в конфигурации

Симптом:
При деплое backend и при пробном запуске Ansible контейнеры postgres и redis
получали статус Recreate, хотя их настройки в docker-compose.yml не менялись.
База на несколько секунд становилась недоступна.

Диагностика:
1. В выводе docker_compose_v2 backend и nginx были Running, а postgres и redis Recreate.
2. В docker-compose.yml образы указаны как postgres:16 и redis:7.
   Это не конкретные версии, а последняя версия ветки 16 и последняя версия ветки 7.
3. На том же сервере работает GitLab Runner. Задача test в CI при каждом пайплайне
   скачивает свежие postgres:16 и redis:7 для временных контейнеров.
4. После очередного пайплайна тег postgres:16 на сервере указывал на более новый образ,
   чем тот, из которого запущена база. Compose видел смену образа и пересоздавал контейнер.
5. В выводе Ansible у работающих контейнеров в поле Image был хеш sha256 без тега,
   тег уже указывал на другой образ.

Исправление:
1. Узнал точные версии работающих контейнеров,
   postgres --version и redis-server --version внутри контейнеров.
2. Зафиксировал их в docker-compose.yml postgres:16.15 и redis:7.4.11.
3. Применил через Ansible. Контейнеры пересоздались один раз из-за смены имени образа,
   версия осталась та же, данные в томах сохранились.
4. Повторный запуск плейбука: changed=0, пересоздания нет.

## 10 Пароль Redis виден в выводе Ansible

Симптом:
Задача «Запустить стек» упала в режиме --check. В выводе ошибки модуль
docker_compose_v2 показал описание всех контейнеров, в том числе
команду Redis с паролем рабочего сервера открытым текстом.
Раньше то же самое произошло при запуске с -v на тестовой машине.

Диагностика:
1. В docker-compose.yml команда Redis была:
   command: redis-server --requirepass ${REDIS_PASSWORD}
2. Compose подставлял значение пароля в команду при создании контейнера.
   Пароль сохранялся в описании контейнера и был виден
   в docker inspect, docker ps --no-trunc и в выводе Ansible.

Исправление:
1. Команда Redis теперь берёт пароль из переменной окружения внутри контейнера
   command: ["sh", "-c", "exec redis-server --requirepass \"$$REDIS_PASSWORD\""]
   environment:
     REDIS_PASSWORD: ${REDIS_PASSWORD}
     REDISCLI_AUTH: ${REDIS_PASSWORD}
   В описании контейнера хранится текст $REDIS_PASSWORD, а не значение.
   $$ в compose-файле означает одиночный $, чтобы Compose не подставлял значение сам.
2. Сменил пароль Redis в Vault, так как старый попал в вывод.
3. Проверил защиту: redis-cli ping с паролем — PONG,
   без пароля — NOAUTH Authentication required.
4. Задаче создания .env добавил diff: false, чтобы --diff не показывал содержимое.

