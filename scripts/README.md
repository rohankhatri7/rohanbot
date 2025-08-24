# Data Processing Scripts

## 📁 Overview

Utility scripts for processing Discord data and preparing training datasets.

## 🔧 Scripts

### `process_discord.py`
Processes raw Discord message exports into structured data.

**Usage:**
```bash
python process_discord.py --input data/Messages/ --output data/processed/
```

**Features:**
- Extracts conversations from Discord JSON exports
- Filters spam and low-quality messages
- Groups messages by conversation threads
- Removes sensitive information

### `prepare_finetune.py`
Converts processed Discord data into training format for fine-tuning.

**Usage:**
```bash
python prepare_finetune.py --input data/processed/ --output finetune_output/
```

**Features:**
- Creates instruction-response pairs
- Formats data for PEFT training
- Applies length filtering
- Generates JSONL training files

## 📊 Data Flow

```
Raw Discord Exports → process_discord.py → Structured Data → prepare_finetune.py → Training Data
```

1. **Raw Data**: Discord message exports (JSON format)
2. **Processed Data**: Clean, structured conversations
3. **Training Data**: Formatted instruction-response pairs

## ⚙️ Configuration

### Environment Variables
- `DATA_INPUT_PATH`: Path to raw Discord data
- `DATA_OUTPUT_PATH`: Path for processed output
- `MIN_MESSAGE_LENGTH`: Minimum message length (default: 10)
- `MAX_MESSAGE_LENGTH`: Maximum message length (default: 512)

### Processing Options
- `--filter-bots`: Remove bot messages
- `--min-quality`: Minimum message quality score
- `--preserve-threads`: Keep conversation threading
- `--anonymize`: Remove usernames and IDs
