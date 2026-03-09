# Production Deployment Guide (Ubuntu 22.04 LTS)

Follow these steps to deploy the institutional quant infrastructure on a bare-metal server or VPS (AWS/GCP/DigitalOcean).

## 1. System Preparation
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl vim git htop fail2ban ufw firewall-cmd

# Secure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # Open SSH limit ideally to Whitelisted IP
sudo ufw enable
```

## 2. Docker & Compose Installation
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install plugins
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 3. Clone and Setup Environment
```bash
git clone <repository_url> quantbot-infra
cd quantbot-infra

cp .env.example .env
nano .env # Configure security keys, DB passwords, and Hyperliquid keys securely
```

## 4. Spin Up Environment
```bash
# Build network and images
docker compose build

# Deploy entirely detached
docker compose up -d

# Verify all 10 containers are running safely
docker compose ps
```

## 5. Security & Fail2Ban
Configure fail2ban to prevent brute force Nginx DDOS attempts:
```bash
# /etc/fail2ban/jail.local
[nginx-http-auth]
enabled  = true
filter   = nginx-http-auth
port     = http,https
logpath  = /var/log/nginx/error.log
```
