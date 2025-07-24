# Telegram Anti-Spam Bot

A Telegram bot that protects channels from spam by requiring new members to solve emoji challenges and using AI-powered content analysis.

## Features

- **Emoji Challenges**: New members must select the correct emoji from 13 different questions
- **AI Spam Detection**: Uses DeepSeek AI to analyze first 5 messages from new users
- **Automatic Moderation**: Kicks and bans users who fail challenges or send spam
- **Russian Localization**: All messages and challenges in Russian
- **Comprehensive Logging**: Structured JSON logs with rotation
- **Health Check**: Built-in HTTP server for monitoring
- **Modular Architecture**: Clean, organized codebase with separated concerns

## Project Structure

```
telegram_bot/
├── bot.py              # Main bot logic and handlers
├── config.py           # Centralized configuration
├── messages.py         # UI messages and emoji challenges
├── storage.py          # SQLite database operations
├── requirements.txt    # Python dependencies
├── setup.cfg          # Flake8 configuration
├── db/                 # Database files
│   └── challenges.db   # SQLite database
├── gpt/                # AI/GPT functionality
│   └── deepseek.py     # DeepSeek API integration
└── logs/               # Log files directory
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export DEEPSEEK_API_KEY="your_deepseek_api_key"  # Optional, for AI spam detection
   ```

3. **Bot Permissions**: Ensure your bot has admin rights in the channel with permissions to:
   - Delete messages
   - Restrict members
   - Ban users

## Configuration

### Main Configuration (`config.py`)

All bot settings are centralized in `config.py`:

- **Debug Settings**: `DEBUG_MODE`, `LOG_LEVEL`
- **Bot Settings**: `BOT_TOKEN`, `HTTP_PORT`, `MAX_ATTEMPTS`
- **DeepSeek API**: `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`
- **Spam Detection**: `SPAM_TRACKING_MESSAGES`, `SPAM_TRACKING_DURATION`, custom prompt

### Production vs Development

For production, edit `config.py`:
```python
DEBUG_MODE = False      # Disable debug logging
LOG_LEVEL = logging.INFO  # Reduce log verbosity
```

For development:
```python
DEBUG_MODE = True         # Enable debug logging
LOG_LEVEL = logging.DEBUG # Full log details
```

## How It Works

1. **New Member Joins**: Bot restricts the user and sends a random emoji challenge
2. **Challenge Response**: User has 60 seconds to select the correct emoji from 4 options
3. **Success**: User gets full access and is monitored for spam (first 5 messages)
4. **AI Analysis**: DeepSeek AI evaluates messages using a custom Russian prompt for HOA communities
5. **Auto-Moderation**: Spam detection triggers automatic ban and cleanup

## Features in Detail

### Emoji Challenges (13 variations)
- 🍎 Fruit, 🐱 Animal, 🚗 Transport, 🍕 Food
- 🏠 Building, 🌳 Plant, ⚽ Sports, 📚 Reading  
- ☀️ Weather, 🎸 Music, 👕 Clothing, ☕ Drinks, 😊 Emotions

### AI Spam Detection
- **Context-Aware**: Tuned for HOA/community discussions
- **Intelligent**: Distinguishes between neighbor help and commercial spam
- **Russian Language**: Native Russian prompt and analysis
- **Conservative**: Allows community discussion while blocking obvious spam
- **Modular**: Separated into dedicated `gpt/deepseek.py` module

## API Requirements

### Telegram Bot API
- Create bot via [@BotFather](https://t.me/BotFather)
- Bot must be admin in the target supergroup

### DeepSeek API (Optional)
- Sign up at [platform.deepseek.com](https://platform.deepseek.com)
- Get API key for AI-powered spam detection
- Without API key: bot runs in basic protection mode (emoji challenges only)

## Running

```bash
python bot.py
```

### Startup Messages
```
✅ DeepSeek API connection successful - spam detection enabled
🛡️ Full protection: Emoji challenges + AI spam detection
Bot is ready to process updates
```

Or without DeepSeek:
```
📝 Basic protection mode (no AI spam detection)  
🛡️ Basic protection: Emoji challenges only
```

## Data Storage

- **Database Location**: `db/challenges.db`
- **Format**: SQLite database
- **Tables**: Challenges, tracked users, spam monitoring
- **Backup**: Automatic with database file

## Logging

- **Location**: `logs/` directory
- **Format**: Structured JSON logs
- **Rotation**: Automatic log rotation
- **Levels**: Configurable via `config.py`

## Health Monitoring

HTTP health endpoint available at:
```
http://localhost:8080/health
```

Returns bot status and last activity information.

## Development

The modular structure makes development easier:

- **Add new AI providers**: Create new files in `gpt/` directory
- **Extend storage**: Modify `storage.py` for new data types
- **Update messages**: Edit `messages.py` for new languages/content
- **Adjust configuration**: Centralized in `config.py` 