# Telegram Group Protection Bot

A Telegram bot that protects groups from spam by challenging new users with simple emoji questions.

## Features

- Auto-restricts new members until they solve an emoji challenge
- 3-minute timeout with 2 attempts allowed
- Automatic cleanup of expired messages
- Built-in health monitoring endpoint

## Quick Start

### Prerequisites
- Python 3.9+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Admin permissions in your supergroup

### Installation

1. **Setup**:
   ```bash
   git clone <repository-url>
   cd telegram_bot
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

3. **Run**:
   ```bash
   python bot.py
   ```

## How It Works

1. New member joins → Bot restricts them (read-only)
2. Bot sends emoji challenge (e.g., "Which one is a fruit?" with 🍎🚗🏠📱 options)
3. User clicks correct answer → Gets full permissions
4. Wrong answer or timeout → User is removed

## Configuration

- `TELEGRAM_BOT_TOKEN` - Bot token (required)
- `HTTP_PORT` - Health endpoint port (default: 8080)

### Debug Mode
Create `test_config.py`:
```python
DEBUG_MODE = True
LOG_LEVEL = logging.DEBUG
```

## Bot Permissions Required

- Restrict members
- Ban users  
- Delete messages
- Send messages

## Important Notes

- **Only works in supergroups** (not regular groups)
- Bot needs admin permissions
- Messages auto-delete after completion

## Troubleshooting

- **Bot not working**: Check admin permissions and supergroup status
- **Health endpoint**: Available at `http://localhost:8080/health`
- **Logs**: Check `logs/` directory for errors 