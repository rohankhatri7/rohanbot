# Manual Setup Commands for EC2 Instance
# Run these commands one by one on ubuntu@13.56.248.35

## 1. Update System
```bash
sudo apt-get update -y
sudo apt-get upgrade -y
```

## 2. Install Docker
```bash
# Install prerequisites
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker ubuntu

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker
```

## 3. Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 4. Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/rohankhatri7/rohanbot.git rohanai
cd rohanai
```

## 5. Setup Environment
```bash
# Create .env file
cp .env.example .env

# Edit with your tokens
nano .env
```

**Add your Discord bot token to the .env file:**
```
DISCORD_BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE
HUGGINGFACE_TOKEN=YOUR_HF_TOKEN_HERE
API_HOST=0.0.0.0
API_PORT=8000
```

## 6. Setup Firewall
```bash
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
```

## 7. Build and Start Services
```bash
# Log out and back in to apply docker group membership
exit
# SSH back in: ssh -i your-key.pem ubuntu@13.56.248.35

cd /home/ubuntu/rohanai

# Build and start containers
docker-compose up --build -d
```

## 8. Verify Setup
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs api
docker-compose logs bot

# Test API
curl http://localhost:8000/
```

## 9. Setup Auto-restart (Optional)
```bash
# Create systemd service
sudo tee /etc/systemd/system/rohanai.service > /dev/null <<EOF
[Unit]
Description=RohanAI Discord Bot Application
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/rohanai
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
TimeoutStartSec=300
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable rohanai.service
sudo systemctl start rohanai.service
```

## 10. Monitoring
```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== RohanAI Status ==="
docker-compose ps
echo "=== API Health ==="
curl -s http://localhost:8000/ || echo "API not responding"
echo ""
echo "=== System Resources ==="
free -h
df -h
EOF

chmod +x monitor.sh

# Run monitoring
./monitor.sh
```

Your RohanAI services will be available at:
- http://13.56.248.35:8000/ (API health check)
- http://13.56.248.35:8000/api/chat (Chat endpoint)
- Discord bot will be online automatically
