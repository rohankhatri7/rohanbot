# AWS EC2 Deployment Guide for RohanAI

This guide will help you deploy RohanAI (Discord bot with fine-tuned TinyLlama) on AWS EC2.

## 🚀 Quick Deploy (Recommended)

### Option 1: Using CloudFormation (Automated)

1. **Create AWS Stack**:
   ```bash
   aws cloudformation create-stack \
     --stack-name rohanai-stack \
     --template-body file://deployment/cloudformation.yml \
     --parameters ParameterKey=KeyPairName,ParameterValue=your-key-pair \
                  ParameterKey=InstanceType,ParameterValue=t3.medium \
     --capabilities CAPABILITY_IAM
   ```

2. **Get the public IP**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name rohanai-stack \
     --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
     --output text
   ```

3. **SSH to the instance**:
   ```bash
   ssh -i your-key-pair.pem ubuntu@<PUBLIC_IP>
   ```

4. **Run the deployment script**:
   ```bash
   sudo ./deploy-aws.sh
   ```

### Option 2: Manual Setup

1. **Launch EC2 Instance**:
   - **AMI**: Ubuntu Server 24.04 LTS (ami-014e30c8a36252ae5)
   - **Instance Type**: t3.medium or larger
   - **Security Groups**: Allow ports 22, 80, 443, 8000
   - **Storage**: 20GB minimum

2. **Connect to instance**:
   ```bash
   ssh -i your-key-pair.pem ubuntu@<EC2_PUBLIC_IP>
   ```

3. **Run deployment**:
   ```bash
   wget https://raw.githubusercontent.com/rohankhatri7/rohanbot/main/deployment/deploy-aws.sh
   chmod +x deploy-aws.sh
   sudo ./deploy-aws.sh
   ```

## 🔧 Configuration

### Environment Variables

Edit `/home/ubuntu/rohanai/.env`:
```bash
sudo nano /home/ubuntu/rohanai/.env
```

Required variables:
```env
DISCORD_BOT_TOKEN=your_actual_token_here
HUGGINGFACE_TOKEN=your_token_here
MODEL_PATH=./models/tinyllama-finetuned
ENVIRONMENT=production
```

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section
4. Copy the token and add to `.env`
5. Invite bot to your server with these permissions:
   - Send Messages
   - Read Message History
   - Use Slash Commands

## 📊 Monitoring & Management

### Check Service Status
```bash
cd /home/ubuntu/rohanai
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f bot
```

### Restart Services
```bash
docker-compose restart
```

### Health Check
```bash
./monitor.sh
```

### System Monitoring
```bash
# Check resources
htop
df -h
free -h

# Check Docker stats
docker stats
```

## 🛠️ Troubleshooting

### Common Issues

**Bot not responding**:
```bash
# Check bot logs
docker-compose logs bot

# Restart bot
docker-compose restart bot
```

**API not loading model**:
```bash
# Check if model files exist
ls -la models/tinyllama-finetuned/

# Check API logs
docker-compose logs api

# Restart with fresh containers
docker-compose down
docker-compose up --build -d
```

**High memory usage**:
```bash
# Monitor memory
free -h
docker stats

# Restart services to free memory
docker-compose restart
```

### Log Locations

- Application logs: `/home/ubuntu/rohanai/logs/`
- Docker logs: `docker-compose logs`
- System logs: `/var/log/`
- Monitoring logs: `/home/ubuntu/rohanai/logs/monitor.log`

## 🔒 Security Best Practices

### 1. Restrict SSH Access
```bash
# Edit security group to allow only your IP
# In AWS Console: EC2 → Security Groups → Edit inbound rules
```

### 2. Set up SSL (Optional)
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Regular Updates
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Update application
cd /home/ubuntu/rohanai
git pull origin main
docker-compose up --build -d
```

## 📈 Scaling & Optimization

### Upgrade Instance
```bash
# Stop services
docker-compose down

# In AWS Console: Stop instance → Change instance type → Start
# Then restart services
docker-compose up -d
```

### Add Auto Scaling (Advanced)
- Use AWS Auto Scaling Groups
- Set up Application Load Balancer
- Configure CloudWatch alarms

## 🌐 Domain Setup (Optional)

1. **Register domain** (e.g., rohanai.example.com)
2. **Point A record** to your EC2 Elastic IP
3. **Update Nginx config** with your domain
4. **Setup SSL certificate**:
   ```bash
   sudo certbot --nginx -d rohanai.example.com
   ```

## 📱 Testing Your Deployment

### API Test
```bash
curl http://your-ec2-ip:8000/
curl -X POST http://your-ec2-ip:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello!"}]}'
```

### Discord Test
1. Mention your bot in Discord: `@rohanai hello`
2. Bot should respond with AI-generated text

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs: `docker-compose logs`
3. Run health check: `./monitor.sh`
4. Check GitHub issues
5. Ensure all environment variables are set correctly

## 💰 Cost Estimation

**Monthly AWS costs** (approximate):
- t3.medium instance: ~$25/month
- Elastic IP: ~$3.65/month
- Data transfer: Variable
- **Total**: ~$30-40/month

**To reduce costs**:
- Use t3.small for lighter workloads
- Stop instance when not in use
- Use Spot instances for development
