# convert_to_modelfile.py
import json
from pathlib import Path

def convert_to_modelfile(input_file, output_file, max_messages=1000):
    with open(input_file, 'r', encoding='utf-8') as f:
        conversations = [json.loads(line) for line in f if line.strip()]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write the base configuration
        f.write("""# Modelfile
FROM llama3

# Set the system prompt
SYSTEM \"""
You are a helpful assistant that responds in a casual, conversational style.
\"""

# Set parameters
PARAMETER num_ctx 4096

# Training parameters
PARAMETER num_epochs 3
PARAMETER learning_rate 0.0001
PARAMETER batch_size 4

""")
        
        # Add training messages
        count = 0
        for conv in conversations[:max_messages]:
            for msg in conv.get('messages', []):
                role = msg.get('role', '')
                content = msg.get('content', '').replace('"', '\\"').replace('\n', ' ')
                if role and content:
                    f.write(f'MESSAGE {role} "{content}"\n')
                    count += 1
                    if count >= max_messages * 2:  # *2 because each conversation has at least 2 messages
                        break
            if count >= max_messages * 2:
                break
        
        print(f"Converted {count} messages to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert training data to Modelfile format')
    parser.add_argument('input_file', help='Path to the finetune_data.jsonl file')
    parser.add_argument('--output', '-o', default='Modelfile.train',
                      help='Output file path (default: Modelfile.train)')
    parser.add_argument('--max-messages', type=int, default=1000,
                      help='Maximum number of message pairs to include (default: 1000)')
    
    args = parser.parse_args()
    convert_to_modelfile(args.input_file, args.output, args.max_messages)