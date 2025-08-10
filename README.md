# RohanAI - Discord Bot with Fine-tuned TinyLlama

A Discord bot powered by a fine-tuned TinyLlama model, containerized with Docker and deployable on AWS EC2.

## 🏗️ Project Structure

```
rohanai/
├── api/                    # FastAPI backend
│   ├── main.py            # Main API server with model inference
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # API container configuration
├── bot/                   # Discord bot
│   ├── index.js          # Bot main file
│   ├── package.json      # Node.js dependencies
│   └── Dockerfile        # Bot container configuration
├── models/               # Trained models
│   └── tinyllama-finetuned/  # Your fine-tuned model
├── data/                 # Training and processed data
├── deployment/           # AWS deployment configurations
├── docker-compose.yml    # Multi-service orchestration
├── .env.example          # Environment variables template
└── README.md            # This file
```

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone <your-repo>
cd rohanai

# Copy environment template
cp .env.example .env
# Edit .env with your tokens

# Start with Docker Compose
docker-compose up --build
```

### AWS EC2 Deployment
```bash
# Run deployment script
./deployment/deploy-aws.sh
```

## 🔧 Configuration

Set these environment variables in `.env`:
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `HUGGINGFACE_TOKEN`: Hugging Face API token (optional)
- `MODEL_PATH`: Path to your fine-tuned model

## 📦 Services

- **API**: FastAPI server with TinyLlama model inference (Port 8000)
- **Bot**: Discord bot client
- **Nginx**: Reverse proxy and load balancer (Port 80/443)

## 🔑 Environment Variables

See `.env.example` for all required variables.
