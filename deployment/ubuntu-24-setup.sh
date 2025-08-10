#!/bin/bash

# Quick Setup Script for Ubuntu 24.04 LTS
# Optimized for ami-014e30c8a36252ae5

set -e

echo "🚀 Setting up RohanAI on Ubuntu 24.04 LTS..."
echo "📋 AMI: ami-014e30c8a36252ae5"

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install essential packages
echo "📦 Installing essential packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    wget \
    git \
    htop \
    unzip \
    software-properties-common

# Install Docker using the official Docker repository
echo "🐳 Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose (standalone)
echo "🐳 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify Docker installation
echo "✅ Verifying Docker installation..."
sudo systemctl enable docker
sudo systemctl start docker

# Clone or update the RohanAI repository
echo "📁 Setting up RohanAI project..."
cd /home/ubuntu

if [ -d "rohanai" ]; then
    echo "📁 Updating existing repository..."
    cd rohanai
    git pull origin main
    cd ..
else
    echo "📁 Cloning RohanAI repository..."
    git clone https://github.com/rohankhatri7/rohanbot.git rohanai
fi

# Set proper ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/rohanai

# Navigate to project directory
cd /home/ubuntu/rohanai

# Create environment file from template
echo "🔧 Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file with your tokens:"
    echo "   nano .env"
    echo ""
    echo "Required tokens:"
    echo "   - DISCORD_BOT_TOKEN (from Discord Developer Portal)"
    echo "   - HUGGINGFACE_TOKEN (optional, from huggingface.co)"
    echo ""
    echo "Example:"
    echo "   DISCORD_BOT_TOKEN=MTM5MD..."
    echo "   HUGGINGFACE_TOKEN=hf_..."
    echo ""
    read -p "Press Enter when you're ready to edit the .env file..."
    nano .env
fi

# Create necessary directories
mkdir -p logs data/processed deployment/ssl

# Setup firewall (UFW)
echo "🔒 Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp

# Setup log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/rohanai > /dev/null <<EOF
/home/ubuntu/rohanai/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
EOF

# Build and start the application
echo "🏗️  Building and starting RohanAI services..."
echo "This may take a few minutes..."

# Use newgrp to apply docker group membership
newgrp docker <<EONG
docker-compose down 2>/dev/null || true
docker-compose up --build -d
EONG

# Create monitoring script
echo "📊 Setting up monitoring..."
cat > /home/ubuntu/rohanai/monitor.sh << 'EOF'
#!/bin/bash
echo "=== RohanAI Status Report ==="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "Uptime: $(uptime)"
echo ""
echo "=== Docker Services ==="
cd /home/ubuntu/rohanai
docker-compose ps
echo ""
echo "=== Recent Logs ==="
echo "--- API Logs (last 5 lines) ---"
docker-compose logs --tail=5 api 2>/dev/null || echo "API service not running"
echo ""
echo "--- Bot Logs (last 5 lines) ---"
docker-compose logs --tail=5 bot 2>/dev/null || echo "Bot service not running"
echo ""
echo "=== System Resources ==="
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h /
echo ""
echo "=== API Health Check ==="
curl -s -f http://localhost:8000/ && echo "✅ API is healthy" || echo "❌ API is not responding"
echo ""
echo "=== End of Report ==="
EOF

chmod +x /home/ubuntu/rohanai/monitor.sh

# Setup monitoring cron job
echo "⏰ Setting up automated monitoring..."
(crontab -l 2>/dev/null; echo "*/10 * * * * /home/ubuntu/rohanai/monitor.sh >> /home/ubuntu/rohanai/logs/monitor.log 2>&1") | crontab -

# Setup systemd service for auto-restart
echo "🔄 Setting up auto-restart service..."
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

sudo systemctl daemon-reload
sudo systemctl enable rohanai.service

# Final status check
echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🔍 Status Check:"
sleep 10  # Give services time to start

cd /home/ubuntu/rohanai
newgrp docker <<EONG
docker-compose ps
echo ""
echo "🌐 Your RohanAI services should be available at:"
echo "   API Health: http://$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo 'YOUR_EC2_IP'):8000/"
echo "   API Chat: http://$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo 'YOUR_EC2_IP'):8000/api/chat"
echo ""
echo "🤖 Your Discord bot should now be online!"
echo ""
echo "📊 Useful commands:"
echo "   ./monitor.sh                    # Run health check"
echo "   docker-compose logs -f          # View live logs"
echo "   docker-compose restart          # Restart services"
echo "   sudo systemctl status rohanai   # Check service status"
echo ""
echo "📝 Log files:"
echo "   tail -f logs/monitor.log        # Monitoring logs"
echo "   docker-compose logs api         # API logs"
echo "   docker-compose logs bot         # Bot logs"
EONG

echo ""
echo "🎉 RohanAI is now running on Ubuntu 24.04 LTS!"
echo "📋 AMI: ami-014e30c8a36252ae5"
