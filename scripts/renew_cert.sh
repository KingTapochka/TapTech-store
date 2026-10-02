set -e
cd /home/devops/computer-store
docker compose run --rm certbot renew --quiet
docker compose exec -T nginx nginx -s reload
