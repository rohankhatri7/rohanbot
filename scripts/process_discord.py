# data_processing/process_discord.py
import json
import re
import sys
from pathlib import Path
from datetime import datetime

def clean_message(content):
    """Clean message content by removing mentions, emojis, etc."""
    if not content or not isinstance(content, str):
        return ""
    # Remove user mentions
    content = re.sub(r'<@!?\d+>', '', content)
    # Remove channel mentions
    content = re.sub(r'<#\d+>', '', content)
    # Remove custom emojis
    content = re.sub(r'<a?:\w+:\d+>', '', content)
    # Remove URLs
    content = re.sub(r'https?://\S+', '', content)
    # Remove multiple spaces and trim
    content = ' '.join(content.split())
    return content.strip()

def process_discord_export(export_path, output_file):
    messages = []
    processed_count = 0
    error_count = 0
    file_count = 0
    
    export_path = Path(export_path)
    message_files = list(export_path.rglob('*.json'))
    print(f"Found {len(message_files)} JSON files to process...")
    
    try:
        from tqdm import tqdm
        file_iterator = tqdm(message_files, desc="Processing files")
    except ImportError:
        print("tqdm not available, showing simple progress...")
        file_iterator = message_files
    
    for json_file in file_iterator:
        try:
            with open(json_file, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
                file_count += 1
                
                # Skip if not a list of messages
                if not isinstance(data, list):
                    continue
                
                for msg in data:
                    if not isinstance(msg, dict):
                        continue
                        
                    # Get message content
                    content = msg.get('Contents') or msg.get('content') or ''
                    if not content:
                        continue
                        
                    # Clean the content
                    cleaned = clean_message(content)
                    if not cleaned:
                        continue
                    
                    # Get timestamp
                    timestamp = msg.get('Timestamp') or msg.get('timestamp') or ''
                    
                    # Get author info (if available)
                    author_id = msg.get('AuthorID') or msg.get('author_id') or ''
                    author_name = msg.get('AuthorName') or msg.get('author_name') or 'unknown'
                    
                    # Add to messages
                    messages.append({
                        'text': cleaned,
                        'timestamp': timestamp,
                        'author_id': str(author_id),
                        'author_name': str(author_name),
                        'channel': str(json_file.parent.name),
                        'source': 'discord'
                    })
                    processed_count += 1
                    
            # Print progress
            if not isinstance(file_iterator, list) or file_count % 10 == 0:
                print(f"Processed {processed_count} messages from {file_count} files...", end='\r')
                        
        except json.JSONDecodeError as e:
            error_count += 1
            print(f"\nError decoding JSON in {json_file}: {str(e)}")
        except Exception as e:
            error_count += 1
            print(f"\nError processing {json_file}: {str(e)}")
    
    print(f"\n\nProcessing complete!")
    print(f"Processed {file_count} files")
    print(f"Found {processed_count} valid messages")
    print(f"Encountered {error_count} errors")
    
    if messages:
        try:
            # Sort by timestamp if available
            if any('timestamp' in msg and msg['timestamp'] for msg in messages):
                messages.sort(key=lambda x: x.get('timestamp', ''))
                print("Messages sorted by timestamp")
        except Exception as e:
            print(f"Warning: Could not sort messages by timestamp: {str(e)}")
        
        # Save to output file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for msg in messages:
                f.write(json.dumps(msg, ensure_ascii=False) + '\n')
        
        print(f"Output saved to {output_file}")
        
        # Show sample of processed messages
        print("\nSample of processed messages:")
        for msg in messages[:5]:  # Show first 5 messages
            print(f"[{msg.get('timestamp', 'no timestamp')}] {msg['author_name']}: {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}")
    else:
        print("No messages were processed. Check the input files and their structure.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Discord message export')
    parser.add_argument('export_path', help='Path to the Discord export directory')
    parser.add_argument('--output', '-o', default='discord_messages_processed.jsonl',
                      help='Output file path (default: discord_messages_processed.jsonl)')
    
    args = parser.parse_args()
    process_discord_export(args.export_path, args.output)