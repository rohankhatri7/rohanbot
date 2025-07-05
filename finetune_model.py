import json
import os
from pathlib import Path
import random
from typing import List, Dict, Any

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load a .jsonl file into a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def combine_datasets(finetune_path: str, discord_path: str, output_path: str, max_examples: int = None):
    """Combine finetune data and Discord messages into a single dataset."""
    # Load both datasets
    try:
        finetune_data = load_jsonl(finetune_path)
        print(f"Loaded {len(finetune_data)} examples from {finetune_path}")
    except FileNotFoundError:
        print(f"Warning: {finetune_path} not found. Using empty list.")
        finetune_data = []
    
    try:
        discord_data = load_jsonl(discord_path)
        print(f"Loaded {len(discord_data)} examples from {discord_path}")
    except FileNotFoundError:
        print(f"Warning: {discord_path} not found. Using empty list.")
        discord_data = []
    
    # Combine datasets
    combined_data = finetune_data + discord_data
    
    # Shuffle the data
    random.shuffle(combined_data)
    
    # Limit the number of examples if specified
    if max_examples and len(combined_data) > max_examples:
        combined_data = combined_data[:max_examples]
    
    # Save combined dataset
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in combined_data:
            f.write(json.dumps(item) + '\n')
    
    print(f"Saved {len(combined_data)} examples to {output_path}")
    return output_path

def create_modelfile(training_data_path: str, output_path: str, base_model: str = "llama3"):
    """Create an Ollama Modelfile for fine-tuning."""
    # Build initial Modelfile content
    modelfile_content = f"FROM {base_model}\n\n"

    # System prompt for the model (customise as you like)
    system_prompt = (
        "You are Rohan, a helpful and casual AI assistant. You have a friendly and "
        "conversational tone, similar to how a young adult would text. Keep your responses "
        "natural and engaging, and don't be afraid to show personality."
    )

    # Add the SYSTEM instruction (triple-quoted block inside a single-quoted f-string)
    modelfile_content += f'SYSTEM """{system_prompt}"""\n\n'
    
    # Training-data template and parameters
    template = '''
# Training data
TEMPLATE """[
    {
        "role": "system",
        "content": "You are a helpful assistant that responds in a casual, conversational style."
    },\n    {% for message in messages %}\n    {\n        "role": "{{message.role}}",\n        "content": "{{message.content}}"\n    }{% if not loop.last %},{% endif %}\n    {% endfor %}\n]"""

PARAMETER num_ctx 4096
PARAMETER num_thread 8
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
'''
    
    modelfile_content += template
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)
    
    print(f"Created Modelfile at {output_path}")
    return output_path

def main():
    # Define paths
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data" / "processed"
    output_dir = base_dir / "finetune_output"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Input files
    finetune_path = data_dir / "finetune_data.jsonl"
    discord_path = data_dir / "discord_messages.jsonl"
    
    # Output files
    combined_output = output_dir / "combined_training_data.jsonl"
    modelfile_path = output_dir / "Modelfile"
    
    # Step 1: Combine datasets
    print("Combining datasets...")
    combine_datasets(
        finetune_path=str(finetune_path),
        discord_path=str(discord_path),
        output_path=str(combined_output),
        max_examples=80000  # Adjust based on your needs
    )
    
    # Step 2: Create Modelfile
    print("\nCreating Modelfile...")
    create_modelfile(
        training_data_path=str(combined_output),
        output_path=str(modelfile_path),
        base_model="llama3"  # You can change this to your preferred base model
    )
    
    print("\nFine-tuning preparation complete!")
    print(f"To fine-tune your model, run:")
    print(f"cd {output_dir}")
    print("ollama create rohan-style -f Modelfile")
    print("\nThis will create a new model called 'rohan-style' that you can use with your bot.")

if __name__ == "__main__":
    main()
