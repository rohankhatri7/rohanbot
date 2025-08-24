# 🤖 RohanAI - Discord Bot with Fine-tuned TinyLlama

A Discord bot powered by a fine-tuned TinyLlama model, containerized with Docker and deployable on AWS EC2.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Discord Bot Token
- (Optional) Hugging Face Token

### Local Development
```bash
# Clone repository
git clone https://github.com/rohankhatri7/rohanbot.git rohanai
cd rohanai

# Configure environment
cp .env.example .env
# Edit .env with your Discord bot token

# Start services
docker-compose up --build -d

# Check status
curl http://localhost:8000/
```

### AWS Deployment
```bash
# Quick deployment on Ubuntu 24.04 LTS
curl -o setup.sh https://raw.githubusercontent.com/rohankhatri7/rohanbot/main/deployment/ubuntu-24-setup.sh
chmod +x setup.sh
./setup.sh
```

## 🏗️ Architecture

### Services
- **API**: FastAPI backend with TinyLlama inference
- **Bot**: Discord.js client for chat interaction
- **Nginx**: Reverse proxy (production)

### Tech Stack
- **Backend**: Python, FastAPI, Transformers, PEFT
- **Frontend**: Discord.js, Node.js
- **Infrastructure**: Docker, AWS EC2, CloudFormation
- **AI Model**: TinyLlama-1.1B fine-tuned with LoRA

## 📁 Project Structure

```
rohanai/
├── api/                 # FastAPI backend
├── bot/                 # Discord bot client
├── deployment/          # AWS deployment configs
├── training/           # Model training scripts
├── scripts/            # Data processing utilities
├── docs/               # Documentation
└── docker-compose.yml  # Service orchestration
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
DISCORD_BOT_TOKEN=your_discord_bot_token
HUGGINGFACE_TOKEN=your_hf_token  # Optional
API_HOST=0.0.0.0
API_PORT=8000
```

### Discord Bot Setup
1. Create application at https://discord.com/developers/applications
2. Create bot and copy token
3. Invite bot to server with message permissions

## 🚀 Deployment Options

### 1. AWS EC2 (Recommended)
- **Automated**: Use CloudFormation template
- **Manual**: Run Ubuntu setup script
- **Instance**: t3.medium or larger
- **AMI**: Ubuntu Server 24.04 LTS

### 2. Local Docker
```bash
docker-compose up --build -d
```

### 3. Manual Installation
See `deployment/manual-commands.md`

## 📊 API Endpoints

- `GET /` - Health check
- `POST /api/chat` - Chat with AI
- `GET /api/status` - Service status

### Example Chat Request
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## 🤖 Training Your Own Model

### Data Preparation
```bash
cd scripts
python process_discord.py --input ../data/Messages/ --output ../data/processed/
python prepare_finetune.py --input ../data/processed/ --output ../finetune_output/
```

### Model Training
```bash
cd training
python train_tinyllama.py
```

See `training/README.md` for detailed training instructions.

## 🔍 Monitoring

### Health Checks
```bash
# API health
curl http://your-server:8000/

# Container status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f bot
```

### Production Monitoring
- Automated health checks
- Log rotation
- System resource monitoring
- Auto-restart on failure

## 🛠️ Development

### Running Locally
```bash
# API (Terminal 1)
cd api
python -m uvicorn main:app --reload

# Bot (Terminal 2)
cd bot
node index.js
```

### Testing
```bash
# Test API
curl http://localhost:8000/

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

## � Documentation

- **Project Structure**: `docs/PROJECT_STRUCTURE.md`
- **Training Guide**: `training/README.md`
- **Deployment Guide**: `deployment/AWS_DEPLOYMENT.md`
- **API Documentation**: Auto-generated at `http://localhost:8000/docs`

## 🔒 Security

- Environment variables for secrets
- .gitignore for sensitive files
- Docker security best practices
- AWS security groups configuration

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues
- **Docker permission denied**: Add user to docker group
- **API not responding**: Check container logs
- **Bot offline**: Verify Discord token
- **Out of disk space**: Clean Docker images

### Support
- Create issue on GitHub
- Check deployment logs
- Review documentation

---

**Built with ❤️ using TinyLlama, FastAPI, and Discord.js**
