#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! $1 =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  echo "Usage: provision_vm.sh PUBLIC_IPV4" >&2
  exit 2
fi
public_ip=$1

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg openssl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker

if ! swapon --show --noheadings | grep -q .; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

sudo install -d -m 0755 -o "$USER" -g "$USER" /opt/jobtest
tar -xzf /tmp/jobtest_deploy_20261012.tar.gz -C /opt/jobtest
cd /opt/jobtest

if [[ ! -f .env ]]; then
  db_secret=$(openssl rand -hex 32)
  jwt_secret=$(openssl rand -hex 32)
  umask 077
  cat > .env <<EOF
POSTGRES_DB=jobtest
POSTGRES_USER=jobtest
POSTGRES_PASSWORD=${db_secret}
DATABASE_URL=postgresql+psycopg2://jobtest:${db_secret}@db:5432/jobtest
JWT_SECRET_KEY=${jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=["http://${public_ip}","https://jobtest-pfe-iheb.eastus.cloudapp.azure.com","http://localhost:3000"]
REQUEST_LIMIT_PER_MINUTE=60
EMBEDDING_MODEL_EN=all-mpnet-base-v2
EMBEDDING_MODEL_ML=paraphrase-multilingual-mpnet-base-v2
MATCH_THRESHOLD=0.60
LOG_LEVEL=INFO
LLM_ENABLED=true
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:1.5b
OLLAMA_TIMEOUT=120
OLLAMA_CONNECT_TIMEOUT=3
EOF
fi
chmod 600 .env

sudo docker compose --env-file .env config --quiet
sudo docker compose up -d db ollama
sudo docker compose exec -T ollama ollama pull qwen2.5:1.5b
sudo docker compose build api
sudo docker compose build web
sudo docker compose up -d api web caddy
sudo docker compose ps
