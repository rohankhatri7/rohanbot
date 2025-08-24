# RohanAI Project Structure

## 📁 Directory Overview

```
rohanai/
├── api/                    # FastAPI backend service
│   ├── main.py            # Main API application
│   └── requirements.txt   # Python dependencies
├── bot/                   # Discord bot client
│   ├── index.js          # Bot main file
│   └── package.json      # Node.js dependencies
├── deployment/           # Deployment configurations
│   ├── cloudformation.yml # AWS CloudFormation template
│   ├── deploy-aws.sh     # AWS deployment script
│   ├── ubuntu-24-setup.sh # Ubuntu setup automation
│   └── manual-commands.md # Manual deployment guide
├── training/             # Model training scripts
│   ├── prepare_training_data.py
│   ├── train_colab.py
│   ├── train_model.py
│   ├── train_tinyllama.py
│   └── test_model_loading.py
├── scripts/              # Data processing utilities
│   ├── prepare_finetune.py
│   └── process_discord.py
├── data/                 # Data storage
│   ├── Messages/         # Raw Discord messages
│   └── processed/        # Processed training data
├── logs/                 # Application logs
├── docs/                 # Documentation
├── docker-compose.yml    # Multi-service orchestration
├── Dockerfile           # Container definition
├── .env.example         # Environment template
└── README.md           # Project overview
```

## 🚀 Services

### API Service
- **Port**: 8000
- **Health Check**: `GET /`
- **Chat Endpoint**: `POST /api/chat`
- **Status**: `GET /api/status`

### Discord Bot
- Connects to Discord using bot token
- Forwards messages to API service
- Responds with AI-generated content

### Nginx (Production)
- Reverse proxy for API
- SSL termination
- Static file serving

## 🔧 Development

### Local Development
```bash
# Start API
cd api && python -m uvicorn main:app --reload

# Start Bot (separate terminal)
cd bot && node index.js
```

### Docker Development
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🌐 Deployment

### AWS EC2 (Recommended)
1. Use CloudFormation template: `deployment/cloudformation.yml`
2. Or manual setup: `deployment/ubuntu-24-setup.sh`

### Manual Deployment
See `deployment/manual-commands.md` for step-by-step instructions.

## 📝 Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `DISCORD_BOT_TOKEN`: Discord bot authentication
- `HUGGINGFACE_TOKEN`: Optional HF model access
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)

## 🔍 Monitoring

### Health Checks
- API: `curl http://localhost:8000/`
- Docker: `docker-compose ps`
- Logs: `docker-compose logs service_name`

### Production Monitoring
- Automated health checks every 10 minutes
- Log rotation configured
- System resource monitoring
- Auto-restart on failure
