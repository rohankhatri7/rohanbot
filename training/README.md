# Training Documentation

## 🎯 Overview

This directory contains all scripts and configurations for training the TinyLlama fine-tuned model used by RohanAI.

## 📁 Files

### Core Training Scripts

- **`train_tinyllama.py`** - Main training script for TinyLlama model using PEFT/LoRA
- **`train_model.py`** - General model training utilities
- **`train_colab.py`** - Google Colab optimized training script
- **`prepare_training_data.py`** - Data preprocessing and formatting

### Testing & Validation

- **`test_model_loading.py`** - Model loading and inference testing

## 🚀 Training Process

### 1. Data Preparation
```bash
python prepare_training_data.py
```
This script:
- Processes Discord message data
- Formats conversations for training
- Creates JSONL training files
- Applies data cleaning and filtering

### 2. Model Training
```bash
python train_tinyllama.py
```
Training configuration:
- Base model: TinyLlama-1.1B-Chat-v1.0
- Method: PEFT (Parameter Efficient Fine-tuning) with LoRA
- Framework: Transformers + PEFT
- Optimization: 4-bit quantization for memory efficiency

### 3. Model Testing
```bash
python test_model_loading.py
```
Validates:
- Model loading without errors
- Inference capability
- Response generation quality

## ⚙️ Configuration

### Training Parameters
- **Learning Rate**: 2e-4
- **Batch Size**: 4 (with gradient accumulation)
- **LoRA Alpha**: 16
- **LoRA Dropout**: 0.1
- **Max Length**: 512 tokens

### Hardware Requirements
- **Minimum**: 8GB GPU memory
- **Recommended**: 16GB+ GPU memory
- **Google Colab**: T4/V100 GPU runtime

## 📊 Training Data

### Data Sources
- Discord conversation history
- Processed chat interactions
- Formatted as instruction-response pairs

### Data Format
```json
{
  "instruction": "User message or prompt",
  "input": "Additional context (optional)",
  "output": "Expected AI response"
}
```

## 🔍 Model Evaluation

### Metrics Tracked
- Training loss
- Validation perplexity
- Response coherence
- Context understanding

### Monitoring
- Weights & Biases integration
- Real-time loss tracking
- Gradient monitoring
- Memory usage optimization

## 🚀 Using Trained Models

### Model Output Location
Trained models are saved to:
- `../models/tinyllama-finetuned/`
- Includes adapter weights and tokenizer
- Compatible with PEFT loading

### Loading in Production
```python
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# Load fine-tuned adapter
model = PeftModel.from_pretrained(base_model, "path/to/adapter")

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
```

## 📝 Notes

- Training scripts include automatic checkpointing
- Memory optimization for resource-constrained environments
- Supports both local and cloud training
- Model artifacts are excluded from git (see .gitignore)
