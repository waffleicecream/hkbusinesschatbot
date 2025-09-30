# Business Analytics Chatbot

A conversational AI chatbot powered by Claude API that analyzes Ecocutlery product performance data from Amazon business reports.

## Features

- **Semantic Memory Management** - Uses intelligent conversation summarization to maintain context while drastically reducing token usage
- **Persistent Conversations** - Automatically saves and loads conversation history across sessions
- **Token-efficient Architecture**
  - Only sends last 4 message pairs + summaries of older conversations
  - CSV data sent once at start, not repeated with each message
  - Reduces token usage by up to 80% compared to naive approaches
- **Data-driven insights** - Analyzes sales, conversion rates, and product metrics
- **Easy customization** - Separate prompt file for easy behavior modification
- **Usage Statistics** - Track token usage and conversation metrics in real-time

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install anthropic python-dotenv
```

2. Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=your_api_key_here
```

3. Run the chatbot:
```bash
python agent.py
```

## Usage

### Commands
- **Ask questions** - Natural language queries about product performance
- **`stats`** - View token usage and conversation statistics
- **`save`** - Manually save conversation to disk
- **`clear`** - Reset conversation history (fresh start)
- **`quit`** - Exit (auto-saves conversation)

### Example Questions
- "Which product has the highest conversion rate?"
- "What are the top 5 products by revenue?"
- "Compare B2B vs total sales performance"
- "Which products need optimization?"
- "Tell me more about that last product" ← Context is preserved!

## How Token Optimization Works

### Traditional Approach (Inefficient)
```
Every message sends: [System Prompt + CSV Data + All Previous Messages + New Question]
Message 10 = ~50,000 tokens 💸
```

### Our Approach (Optimized)
```
First message: [System Prompt + CSV Data + Question]
Message 2-6: [Initial Context + Recent 4 message pairs + New Question]
Message 7+: [Initial Context + Summary + Recent 4 message pairs + New Question]
Message 10 = ~5,000 tokens ✅ (90% reduction!)
```

### Automatic Summarization
When conversation exceeds 12 messages, older messages are automatically:
1. Summarized into key points by Claude
2. Compressed from ~3000 tokens → ~300 tokens
3. Stored as context while removing verbose details

## Files

- `agent.py` - Main chatbot application with ConversationMemory class
- `prompt.txt` - System prompt defining chatbot behavior
- `Business report.csv` - Product performance data
- `conversation_memory.pkl` - Saved conversation history (auto-generated)
- `.env` - API key (not tracked in git)

## Customization

- **Change behavior**: Edit `prompt.txt` to modify how the chatbot responds
- **Adjust memory size**: Modify `max_recent_messages=4` in agent.py
- **Change model**: Update `model` parameter in agent.py (e.g., claude-3-5-sonnet-20241022)

## Technical Details

The `ConversationMemory` class handles:
- Full conversation history storage
- Automatic summarization when history exceeds thresholds
- Persistent storage using pickle
- Context optimization for API calls
- Token estimation and tracking