# data_processing/prepare_finetune.py
import json
from pathlib import Path

def convert_to_conversation_format(input_file, output_file, system_prompt=None):
    """
    Convert messages to conversation format for fine-tuning.
    Format: {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
    """
    conversations = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        messages = [json.loads(line) for line in f if line.strip()]
    
    # Group messages by channel
    channel_messages = {}
    for msg in messages:
        channel = msg.get('channel', 'default')
        if channel not in channel_messages:
            channel_messages[channel] = []
        channel_messages[channel].append(msg)
    
    # Create conversation pairs within each channel
    for channel, msgs in channel_messages.items():
        # Sort messages by timestamp
        msgs.sort(key=lambda x: x.get('timestamp', ''))
        
        # Create conversation pairs
        for i in range(0, len(msgs) - 1, 2):
            user_msg = msgs[i]
            assistant_msg = msgs[i + 1] if i + 1 < len(msgs) else None
            
            conversation = {"messages": []}
            if system_prompt:
                conversation["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add user message
            if user_msg and user_msg.get('text'):
                conversation["messages"].append({
                    "role": "user",
                    "content": user_msg['text']
                })
                
                # Add assistant message if available
                if assistant_msg and assistant_msg.get('text'):
                    conversation["messages"].append({
                        "role": "assistant",
                        "content": assistant_msg['text']
                    })
                    
                    conversations.append(conversation)
    
    # Save to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + '\n')
    
    print(f"Prepared {len(conversations)} conversation pairs in {output_file}")

def convert_to_modelfile(input_file, output_file, max_examples=50):
    """
    Convert the prepared finetune data to Ollama Modelfile format
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        conversations = [json.loads(line) for line in f if line.strip()]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write the base configuration
        f.write('FROM llama3\n\n')
        f.write('SYSTEM """\n')
        f.write('You are a helpful assistant that responds in a casual, conversational style.\n')
        f.write('"""\n\n')
        f.write('PARAMETER num_ctx 4096\n\n')
        
        # Add training examples
        example_count = 0
        for conv in conversations:
            if example_count >= max_examples * 2:  # *2 because each example has user and assistant messages
                break
                
            messages = conv.get('messages', [])
            for msg in messages:
                role = msg.get('role', '')
                content = msg.get('content', '')
                
                # Skip system messages in the training examples
                if role == 'system':
                    continue
                    
                if role and content:
                    # Clean and format the content
                    content = content.replace('"', '\\"').replace('\n', ' ')
                    if content.strip():  # Only write if there's content after cleaning
                        f.write(f'MESSAGE {role} "{content}"\n')
                        example_count += 1
                        if example_count >= max_examples * 2:
                            break
        
        print(f"Added {example_count//2} conversation pairs to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare data for fine-tuning')
    parser.add_argument('input_file', help='Path to the processed messages file')
    parser.add_argument('--output', '-o', default='Modelfile.personal',
                      help='Output file path (default: Modelfile.personal)')
    parser.add_argument('--max-examples', type=int, default=50,
                      help='Maximum number of conversation pairs to include (default: 50)')
    parser.add_argument('--system-prompt', default='You are a helpful assistant that responds in a casual, conversational style.',
                      help='System prompt to use for fine-tuning')
    
    args = parser.parse_args()
    
    # First convert to conversation format
    temp_file = "temp_conversations.jsonl"
    convert_to_conversation_format(args.input_file, temp_file, args.system_prompt)
    
    # Then convert to Modelfile format
    convert_to_modelfile(temp_file, args.output, args.max_examples)
    
    # Clean up
    Path(temp_file).unlink(missing_ok=True)
    print(f"\nTraining file ready at: {args.output}")
    print(f"To create your model, run: ollama create my-personal-style -f {args.output}")
    print(f"Then test it with: ollama run my-personal-style 'Hey, how are you?'")