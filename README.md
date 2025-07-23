# Telegram Group Protection Bot

A Telegram bot designed to protect groups from spam and unwanted members by challenging new users with simple math problems.

## 🛡️ Features

- **Automatic Member Verification**: New members are automatically restricted and must solve a math challenge
- **Timed Challenges**: Users have 3 minutes to complete the challenge
- **Multiple Attempts**: Up to 2 wrong attempts allowed before removal
- **Anti-Bot Protection**: Prevents automated spam accounts from joining
- **Healthcheck Endpoint**: Built-in HTTP server for monitoring bot status
- **Structured Logging**: JSON logging for analysis and debugging
- **Multi-language Ready**: Easy to translate message strings

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- A Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather))
- Admin permissions in your Telegram group/supergroup

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd telegram_bot
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the bot**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   # Optional: Set custom HTTP port for healthcheck
   export HTTP_PORT="8080"
   ```

5. **Run the bot**:
   ```bash
   python bot.py
   ```

## ⚙️ Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather (required)
- `HTTP_PORT` - Port for healthcheck endpoint (default: 8080)

### Debug Mode

Create a `test_config.py` file for debug features:

```python
DEBUG_MODE = True
LOG_LEVEL = logging.DEBUG
```

When enabled, adds `/debug_join` command to simulate user joins for testing.

## 🔧 How It Works

1. **New Member Detection**: Bot detects when someone joins the group
2. **Immediate Restriction**: New member is restricted (read-only mode)
3. **Math Challenge**: Bot sends a simple addition problem with multiple choice answers
4. **User Response**: Member clicks the correct answer within 3 minutes
5. **Verification**: 
   - ✅ Correct answer → User gets full permissions + welcome message
   - ❌ Wrong answer → User gets another chance (max 2 attempts)
   - ⏰ Timeout → User is automatically removed

## 📊 Monitoring

The bot includes a built-in HTTP server for health monitoring:

- **Health Status**: `GET /health` or `GET /healthcheck`
- **Bot Information**: `GET /`

Example health response:
```json
{
  "status": "running",
  "uptime_seconds": 3600,
  "challenges_processed": 15,
  "errors_count": 0,
  "version": "1.0.0"
}
```

## 📁 Project Structure

```
telegram_bot/
├── bot.py              # Main bot application
├── storage.py          # SQLite database management
├── messages.py         # All text messages (Russian)
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project metadata
├── test_config.py      # Debug configuration (optional)
├── logs/              # Log files directory
└── challenges.db      # SQLite database (created automatically)
```

## 🗂️ Database

The bot uses SQLite to track active challenges:

- **Challenges table**: Stores pending verification challenges
- **Auto-cleanup**: Expired challenges are automatically removed
- **Thread-safe**: Supports concurrent access

## 📝 Logging

Comprehensive logging system with multiple outputs:

- **Console logs**: Real-time monitoring
- **File logs**: Rotating log files in `logs/` directory
- **JSON logs**: Structured data for analysis (`logs/bot_analysis.json`)

Log levels include user actions, errors, and system events.

## 🌐 Localization

Currently in Russian. To add other languages:

1. Copy `messages.py` to `messages_en.py` (or your language code)
2. Translate all message strings
3. Import the appropriate messages module in `bot.py`

## 🔐 Permissions Required

The bot needs these permissions in your group:

- **Restrict members**: To limit new user permissions
- **Ban users**: To remove users who fail challenges
- **Delete messages**: To clean up challenge messages
- **Send messages**: To post challenges and responses

## ⚠️ Important Notes

- **Supergroups Only**: Bot only works in Telegram supergroups (not regular groups)
- **Admin Rights**: Bot must have admin permissions to restrict/ban members
- **Message Cleanup**: Challenge messages are automatically deleted after completion

## 🚨 Troubleshooting

**Bot not responding to new members:**
- Verify bot has admin permissions
- Ensure group is converted to supergroup
- Check bot token is correct

**Health endpoint not accessible:**
- Verify `HTTP_PORT` environment variable
- Check firewall settings if running on server

**Database errors:**
- Ensure write permissions in bot directory
- Check SQLite installation

## 📄 License

This project is open source. See the project files for specific licensing information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the logs in `logs/` directory
- Review error messages in console output
- Ensure all prerequisites are met 