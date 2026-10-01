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
Убрал публикацию порта у backend в docker-compose. Доступ к backend будет только через nginx внутри docker-compose сети. Правила UFW не защищают порты опубликованные docker

## 4 Nginx не находит backend после ошибки с портом 80

Симптом:
Nginx постоянно перезапускается, статус "Restarting". В логах:
"host not found in upstream backend in /etc/nginx/conf.d/default.conf:6"
Backend при этом работает.

Диагностика:
1. При первом запуске nginx упал с ошибкой "failed to bind host port 0.0.0.0:80/tcp: address already in use".
2. Через sudo ss -lntp | grep ':80 ' нашёл, что порт 80 на хосте занят nginx, остановил и отключил автозапуск.
3. Повторный docker compose up -d не пересоздал nginx, а запустил тот же контейнер. Видно по id.
4. По логам entrypoint проходит ("Configuration complete"), падает сам nginx: При чтении proxy_pass не может найти адрес backend.

Исправление:
1. docker compose up -d --force-recreate nginx, контейнер создан заново с новым ID.
2. Проверил через docker network inspect computer-store_default, что все 4 контейнера в одной сети.
3. curl http://localhost/api/health возвращает ответ от backend.



