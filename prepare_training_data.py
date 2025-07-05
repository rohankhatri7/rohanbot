# prepare_training_data.py
import json
import random
from pathlib import Path

def prepare_training_data(messages_path: str, output_path: str, max_examples: int = 40000):
    # Load messages
    with open(messages_path, 'r', encoding='utf-8') as f:
        messages = [json.loads(line) for line in f if line.strip()]
    
    print(f"Total messages loaded: {len(messages)}")
    
    # Shuffle messages to get random distribution
    random.shuffle(messages)
    
    # Group messages into conversation pairs
    training_examples = []
    for i in range(0, len(messages) - 1, 2):
        if i + 1 < len(messages):
            training_examples.append({
                "instruction": messages[i]['text'],
                "input": "",
                "output": messages[i + 1]['text']
            })
        
        # Stop when we have enough examples
        if len(training_examples) >= max_examples:
            break
    
    print(f"Created {len(training_examples)} training examples")
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save training data
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Saved training data to {output_path}")

if __name__ == "__main__":
    prepare_training_data(
        messages_path="data/processed/discord_messages.jsonl",
        output_path="data/processed/training_data_40k.jsonl"
    )