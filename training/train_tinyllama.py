import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset, Dataset
import os
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import wandb
from datetime import datetime

def train():
    # Configuration - Using TinyLlama (1.1B parameters)
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    output_dir = "./tinyllama-finetuned"
    batch_size = 1  # Smaller batch size for CPU
    gradient_accumulation_steps = 8  # Increase to compensate for smaller batch
    num_epochs = 1
    learning_rate = 1e-4  # Slightly lower learning rate for stability
    max_length = 256  # Reduced sequence length for faster training
    max_examples = 2000  # Use even fewer examples for testing
    
    # Initialize wandb for logging
    wandb.init(project="tinyllama-finetuning", name="rohan-style")
    
    # Force CPU training for maximum compatibility
    device = "cpu"
    print("Using device: CPU (MPS/GPU disabled for compatibility)")
    
    # Load tokenizer
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load TinyLlama with CPU optimization
    print(f"Loading {model_name} for CPU training...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,  # Use FP32 for CPU
        device_map=None,  # Disable device map for CPU
        trust_remote_code=True,
        low_cpu_mem_usage=True
    ).to(device)  # Explicitly move to CPU
    
    print(f"✅ Model loaded on {next(model.parameters()).device}")
    
    # Configure LoRA for TinyLlama
    print("\nPreparing LoRA configuration...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Prepare model for training
    print("Preparing model for training...")
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load and prepare the dataset
    print("\nLoading dataset...")
    # For Colab, use the direct path where you uploaded the file
    dataset = load_dataset("json", data_files="finetune_data.jsonl", split="train")
    
    # Use only max_examples for this training run
    if len(dataset) > max_examples:
        print(f"Using only {max_examples} out of {len(dataset)} examples")
        dataset = dataset.select(range(max_examples))
    
    # Tokenization function
    def tokenize_function(examples):
        # Format the messages for chat template
        formatted_examples = [
            tokenizer.apply_chat_template(conv, tokenize=False)
            for conv in examples["messages"]
        ]
        
        # Tokenize the formatted examples
        tokenized = tokenizer(
            formatted_examples,
            max_length=max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )
        
        # Create labels (use -100 for padding tokens)
        tokenized["labels"] = tokenized["input_ids"].clone()
        tokenized["labels"][tokenized["labels"] == tokenizer.pad_token_id] = -100
        
        return tokenized
    
    # Tokenize the dataset
    print("Tokenizing dataset...")
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        batch_size=32,
        remove_columns=dataset.column_names
    )
    
    # Add timestamp for unique run name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"tinyllama-finetune-{timestamp}"
    
    # Training arguments optimized for CPU
    training_args = TrainingArguments(
        output_dir=output_dir,
        run_name=run_name,  # Unique name for this run
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_train_epochs=num_epochs,
        max_steps=100,  # For testing, remove for full training
        weight_decay=0.01,
        fp16=False,  # Disable FP16 for CPU
        logging_steps=1,  # Log every step for visibility
        save_steps=25,  # Save more frequently
        report_to="wandb",
        remove_unused_columns=False,
        warmup_ratio=0.1,
        dataloader_num_workers=0,  # Set to 0 for stability on some systems
        optim="adamw_torch",
        no_cuda=True  # Ensure no CUDA is used
    )
    
    # Check for existing checkpoint
    checkpoint = None
    if os.path.isdir(output_dir):
        checkpoints = [d for d in os.listdir(output_dir) if d.startswith('checkpoint-')]
        if checkpoints:
            checkpoint = os.path.join(output_dir, max(checkpoints, key=lambda x: int(x.split('-')[-1])))
            print(f"\n🔍 Found existing checkpoint: {checkpoint}")
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
    )
    
    # Start training with progress bars
    print("\n🚀 Starting training...")
    print(f"Training on {len(tokenized_dataset)} examples")
    print(f"Batch size: {batch_size} (x{gradient_accumulation_steps} grad accumulation)")
    print(f"Sequence length: {max_length} tokens")
    print(f"Total steps: {training_args.max_steps or (len(tokenized_dataset) * num_epochs) // (batch_size * gradient_accumulation_steps)}")
    
    try:
        train_result = trainer.train(resume_from_checkpoint=bool(checkpoint))
    except KeyboardInterrupt:
        print("\nTraining interrupted. Saving current progress...")
        trainer.save_model(f"{output_dir}_interrupted")
        print(f"Model saved to {output_dir}_interrupted")
        return
    
    # Save the final model
    print("\n💾 Saving model...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Also save as a new version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_dir = f"{output_dir}_v{timestamp}"
    trainer.save_model(versioned_dir)
    tokenizer.save_pretrained(versioned_dir)
    print(f"✅ Model also saved as versioned copy: {versioned_dir}")
    
    # Save training metrics
    metrics = train_result.metrics
    metrics["train_samples"] = len(tokenized_dataset)
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()
    
    print(f"\n✅ Training complete! Model saved to {output_dir}")
    print(f"Training metrics: {metrics}")

if __name__ == "__main__":
    train()
