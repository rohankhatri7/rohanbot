# train_model.py
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
    TrainerCallback
)
from datasets import Dataset
import torch
import json
import os
from pathlib import Path

class CustomDataset(torch.utils.data.Dataset):
    def __init__(self, data, tokenizer, max_length=512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{item['instruction']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{item['output']}<|eot_id|>"
        
        # Tokenize the text
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': encoding['input_ids'].squeeze().clone()
        }

def load_training_data(file_path: str, max_examples: int = None):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip():
                data.append(json.loads(line))
                if max_examples and len(data) >= max_examples:
                    break
    return data

def train():
    # Configuration
    model_name = "meta-llama/Meta-Llama-3-8B"  # Updated to correct model ID
    output_dir = "./llama3-8b-finetuned"
    max_length = 512
    batch_size = 2  # Reduced for memory efficiency
    gradient_accumulation_steps = 4
    learning_rate = 2e-5
    num_train_epochs = 2
    
    # Load tokenizer with special tokens
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        use_fast=True,
        token=True  # This will use your Hugging Face token from login
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Load model with 4-bit quantization to reduce memory usage
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    
    # Load and prepare data
    print("Loading training data...")
    train_data = load_training_data("data/processed/training_data_40k.jsonl")
    train_dataset = CustomDataset(train_data, tokenizer, max_length=max_length)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        save_steps=1000,
        save_total_limit=2,
        logging_steps=100,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_steps=100,
        fp16=True,
        evaluation_strategy="no",
        logging_dir=f"{output_dir}/logs",
        report_to=["tensorboard"],
        optim="paged_adamw_32bit",
        lr_scheduler_type="cosine",
        save_safetensors=True,
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    
    # Start training
    print("Starting training...")
    trainer.train()
    
    # Save the final model
    final_output_dir = f"{output_dir}/final"
    os.makedirs(final_output_dir, exist_ok=True)
    
    print(f"Saving model to {final_output_dir}...")
    trainer.save_model(final_output_dir)
    tokenizer.save_pretrained(final_output_dir)
    
    print("Training completed successfully!")
    print(f"Model saved to: {os.path.abspath(final_output_dir)}")

if __name__ == "__main__":
    train()