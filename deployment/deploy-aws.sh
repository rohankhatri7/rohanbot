#!/bin/bash

# AWS EC2 Deployment Script for RohanAI
# This script sets up Docker, downloads the project, and starts the services

set -e

echo "🚀 Starting RohanAI deployment on AWS EC2..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Install additional tools
sudo apt-get install -y git htop curl wget unzip nginx

# Create project directory
echo "📁 Setting up project directory..."
cd /home/ubuntu
PROJECT_DIR="/home/ubuntu/rohanai"

# Clone or update repository
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Updating existing repository..."
    cd $PROJECT_DIR
    git pull origin main
else
    echo "📁 Cloning repository..."
    git clone https://github.com/rohankhatri7/rohanbot.git rohanai
    cd $PROJECT_DIR
fi

# Set proper ownership
sudo chown -R ubuntu:ubuntu $PROJECT_DIR

# Create environment file
echo "🔧 Setting up environment..."
if [ ! -f .env ]; then
    cp deployment/.env.production .env
    echo "⚠️  Please edit .env with your actual tokens:"
    echo "   nano .env"
    echo ""
    echo "Required variables:"
    echo "   - DISCORD_BOT_TOKEN"
    echo "   - HUGGINGFACE_TOKEN (optional)"
    echo ""
    read -p "Press enter after editing .env file..."
fi

# Create necessary directories
mkdir -p logs
mkdir -p data/processed

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/rohanai > /dev/null <<EOF
$PROJECT_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
EOF

# Setup firewall
echo "🔒 Setting up firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose down || true
docker-compose up --build -d

# Create monitoring script
echo "📊 Creating monitoring script..."
tee $PROJECT_DIR/monitor.sh > /dev/null <<'EOF'
#!/bin/bash
echo "=== RohanAI System Status ==="
date
echo "=== Docker Containers ==="
docker-compose ps
echo "=== Container Logs (last 10 lines) ==="
echo "--- API ---"
docker-compose logs --tail=10 api
echo "--- Bot ---"
docker-compose logs --tail=10 bot
echo "=== System Resources ==="
echo "Disk Usage:"
df -h
echo "Memory Usage:"
free -h
echo "=== API Health Check ==="
curl -s http://localhost:8000/ || echo "API not responding"
EOF

chmod +x $PROJECT_DIR/monitor.sh

# Setup monitoring cron job
echo "⏰ Setting up monitoring..."
(crontab -l 2>/dev/null; echo "*/10 * * * * $PROJECT_DIR/monitor.sh >> $PROJECT_DIR/logs/monitor.log 2>&1") | crontab -

# Setup auto-restart on boot
echo "🔄 Setting up auto-restart..."
sudo tee /etc/systemd/system/rohanai.service > /dev/null <<EOF
[Unit]
Description=RohanAI Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable rohanai.service

echo "✅ Deployment complete!"
echo ""
echo "🔍 Useful commands:"
echo "   docker-compose ps                 # Check service status"
echo "   docker-compose logs -f            # View live logs"
echo "   docker-compose restart            # Restart services"
echo "   $PROJECT_DIR/monitor.sh           # Run health check"
echo ""
echo "🌐 Your services should be available at:"
echo "   API: http://$(curl -s http://checkip.amazonaws.com):8000"
echo "   Health: http://$(curl -s http://checkip.amazonaws.com):8000/"
echo ""
echo "📝 Next steps:"
echo "   1. Configure your Discord bot to use this server"
echo "   2. Set up SSL certificates if needed"
echo "   3. Configure your domain DNS"
echo "   4. Monitor logs: tail -f logs/monitor.log"
