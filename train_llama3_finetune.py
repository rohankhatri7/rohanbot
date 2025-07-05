import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset, Dataset
import os
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import wandb

def train():
    # Configuration
    model_name = "meta-llama/Meta-Llama-3-8B"  # Using the full model name
    output_dir = "./llama3-finetuned"
    batch_size = 4
    gradient_accumulation_steps = 4
    num_epochs = 3
    learning_rate = 2e-5
    max_length = 2048
    
    # Initialize wandb for logging
    wandb.init(project="llama3-finetuning", name="rohan-style-full")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Configure 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Load model with 4-bit quantization
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Configure LoRA
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "down_proj", "up_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Add LoRA adapters
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load and prepare dataset
    def preprocess_function(examples):
        # Format as: "### Instruction: {instruction}\n\n### Response: {output}"
        prompts = []
        for i in range(len(examples["instruction"])):
            prompt = f"### Instruction: {examples['instruction'][i]}\n\n### Response: {examples['output'][i]}"
            prompts.append(prompt)
        return {"text": prompts}
    
    dataset = load_dataset("json", data_files="data/processed/training_data_40k.jsonl", split="train")
    dataset = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # Tokenize the dataset
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length",
            return_tensors="pt"
        )
    
    tokenized_datasets = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"]
    )
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        save_steps=100,
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_train_epochs=num_epochs,
        weight_decay=0.01,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=10,
        report_to="wandb",
        save_total_limit=3,
        fp16=True,
        push_to_hub=False
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    
    # Start training
    print("Starting training...")
    trainer.train()
    
    # Save the final model
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print("Training completed!")
    print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    train()