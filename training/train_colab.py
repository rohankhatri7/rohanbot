import json
from tqdm import tqdm
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
import torch
import os
from datetime import datetime

def train():
    # Model and dataset configuration
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    output_dir = f"./tinyllama-finetuned-10k-{datetime.now().strftime('%Y%m%d-%H%M')}"
    os.makedirs(output_dir, exist_ok=True)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        padding_side="right",
        use_fast=True
    )
    tokenizer.pad_token = tokenizer.eos_token

    # Load model with 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    
    # Prepare for LoRA training
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    
    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Define LoRA config
    lora_config = LoraConfig(
        r=16,  # Rank
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],  # Target attention layers
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Add LoRA adapters
    model = get_peft_model(model, lora_config)
    
    # Print trainable parameters
    model.print_trainable_parameters()

    # Load and prepare dataset
    print("Loading and preparing dataset...")
    
    # Check for data file in common locations
    possible_paths = [
        "finetune_data.jsonl",  # Current directory
        "data/processed/finetune_data.jsonl",  # Local path
        "/content/finetune_data.jsonl",  # Colab root
        "/content/rohanai/finetune_data.jsonl",  # Colab rohanai directory
        "/content/drive/MyDrive/rohanai/finetune_data.jsonl"  # Google Drive
    ]
    
    data_path = None
    for path in possible_paths:
        if os.path.exists(path):
            data_path = path
            print(f"Found dataset at: {os.path.abspath(path)}")
            break
    
    if not data_path:
        # List files in current directory for debugging
        print("Could not find dataset. Current directory contents:")
        print(os.listdir())
        raise FileNotFoundError("Could not find finetune_data.jsonl in any expected location")
    
    try:
        # Load the dataset
        dataset = load_dataset("json", data_files=data_path, split="train")
        print(f"Loaded {len(dataset)} examples")
        
        # Shuffle and select first 10,000 examples
        if len(dataset) > 10000:
            dataset = dataset.shuffle(seed=42).select(range(10000))
            print(f"Selected 10,000 random examples")
        
        # Train/test split (90/10)
        dataset = dataset.train_test_split(test_size=0.1, seed=42)
        
        # Save the exact dataset used for training
        os.makedirs(output_dir, exist_ok=True)
        dataset["train"].to_json(f"{output_dir}/training_data.jsonl")
        dataset["test"].to_json(f"{output_dir}/validation_data.jsonl")
        
        print(f"Training on {len(dataset['train'])} examples, validating on {len(dataset['test'])} examples")
        
    except Exception as e:
        print(f"Error loading dataset: {str(e)}")
        raise

    # Tokenization function
    def tokenize_function(examples):
        # Format the messages for chat template
        formatted_examples = [
            tokenizer.apply_chat_template(conv, tokenize=False)
            for conv in examples["messages"]
        ]
        
        # Tokenize
        tokenized = tokenizer(
            formatted_examples,
            max_length=1024,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )
        
        # Create labels (use -100 for padding tokens)
        tokenized["labels"] = tokenized["input_ids"].clone()
        tokenized["labels"][tokenized["labels"] == tokenizer.pad_token_id] = -100
        
        return tokenized

    # Tokenize datasets
    tokenized_datasets = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["train"].column_names,
        num_proc=4
    )

    # Training arguments (keep minimal, widely supported parameters)
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=8,  # Effective batch size = 4 * 8 = 32
        learning_rate=2e-5,
        weight_decay=0.01,
        warmup_ratio=0.03,
        save_steps=200,
        save_total_limit=3,
        fp16=True,
        logging_steps=10,
        remove_unused_columns=False,
        report_to="none"  # Disable wandb sync if not desired
    )

    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Enable gradient checkpointing to save memory
    model.gradient_checkpointing_enable()

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        data_collator=data_collator,
    )

    # Add custom evaluation callback (evaluates every EVAL_STEPS)
    from transformers import TrainerCallback
    EVAL_STEPS = 100
    
    class EvalCallback(TrainerCallback):
        def __init__(self, eval_steps=EVAL_STEPS):
            self.eval_steps = eval_steps
            self.best_loss = float("inf")
        
        def on_step_end(self, args, state, control, **kwargs):
            if state.global_step > 0 and state.global_step % self.eval_steps == 0:
                metrics = trainer.evaluate()
                val_loss = metrics.get("eval_loss", None)
                if val_loss is not None:
                    print(f"\nStep {state.global_step}: validation loss = {val_loss:.4f}")
                    if val_loss < self.best_loss:
                        self.best_loss = val_loss
                        trainer.save_model(os.path.join(output_dir, "best_model"))
                        print(f"New best model saved (loss {self.best_loss:.4f})")
    
    trainer.add_callback(EvalCallback())

    # Print training configuration
    print("\nTraining configuration:")
    print(f"- Training examples: {len(tokenized_datasets['train'])}")
    print(f"- Validation examples: {len(tokenized_datasets['test'])}")
    print(f"- Batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
    print(f"- Learning rate: {training_args.learning_rate}")
    print(f"- Using mixed precision: {'fp16' if training_args.fp16 else 'no'}")
    print(f"- Model device: {next(model.parameters()).device}")
    print("\nStarting training...")

    # Train the model
    print("Starting training...")
    trainer.train()

    # Save the final model
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")

    # Save training arguments
    with open(os.path.join(output_dir, "training_args.json"), "w") as f:
        json.dump(training_args.to_dict(), f, indent=2)

if __name__ == "__main__":
    train()