"""
Configuration constants for the Telegram Anti-Spam Bot
"""
import os
import logging

# =====================================
# DEBUG & LOGGING CONFIGURATION
# =====================================
DEBUG_MODE = True  # Set to False for production
LOG_LEVEL = logging.DEBUG  # logging.INFO for production
debug_mode = DEBUG_MODE

# =====================================
# BOT CONFIGURATION
# =====================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
HTTP_PORT = int(os.getenv("HTTP_PORT", "10000"))  # HTTP server port

# Challenge settings
MAX_ATTEMPTS = 2  # Maximum number of wrong attempts before kicking user
CHALLENGE_TIMEOUT = 180  # Challenge timeout in seconds (3 minutes)

# =====================================
# CHAT RESTRICTIONS
# =====================================
# List of allowed chat IDs (as strings or integers)
# Set to empty list [] to allow all chats
# Example: ALLOWED_CHAT_IDS = [-1001234567890, -1009876543210]
ALLOWED_CHAT_IDS = []

# =====================================
# DEEPSEEK API CONFIGURATION
# =====================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# =====================================
# SPAM DETECTION CONFIGURATION
# =====================================
SPAM_DETECTION_ENABLED = True
SPAM_TRACKING_MESSAGES = 5  # Number of messages to track per new user
SPAM_TRACKING_DURATION = 24 * 60 * 60  # 24 hours in seconds

SPAM_DETECTION_PROMPT = """
Ты - бот модератор Telegram канала товарищества собственников жилых домов, \
где люди обсуждают вопросы ЖКХ, дома, двора и соседства.

ЗАДАЧА: Определи, является ли сообщение спамом/рекламой.

СЧИТАЕТСЯ СПАМОМ:
• Прямая реклама товаров/услуг с ценами, контактами, призывами купить
• Предложения работы/подработки/заработка
• Ссылки на внешние ресурсы/каналы/группы
• Финансовые схемы, инвестиции, криптовалюта
• Многоуровневый маркетинг (МЛМ)
• Повторяющиеся однотипные сообщения

НЕ ЯВЛЯЕТСЯ СПАМОМ:
• Обсуждение проблем дома/двора/ЖКХ
• Поиск/предложение помощи соседям (ремонт, присмотр за животными и т.д.)
• Продажа/обмен личных вещей между соседями
• Рекомендации мастеров/услуг от соседей (без навязывания)
• Обычное общение, даже с нецензурной лексикой
• Новости района/города

Сообщение: "{message}"

Ответь только "SPAM" или "CLEAN". Будь снисходительным к соседскому общению, \
строгим к коммерции.
"""

# =====================================
# ADMIN CONFIGURATION
# =====================================
# List of admin user IDs who can use admin commands like /health
# Set via environment variable ADMIN_USER_IDS (comma-separated)
# Example: ADMIN_USER_IDS="123456789,987654321"
ADMIN_USER_IDS_STR = os.getenv("ADMIN_USER_IDS", "")

# Parse admin user IDs from environment variable
ADMIN_USER_IDS = []
if ADMIN_USER_IDS_STR:
    try:
        ADMIN_USER_IDS = [
            int(uid.strip()) for uid in ADMIN_USER_IDS_STR.split(",") if uid.strip()
        ]
        print(f"✅ Loaded {len(ADMIN_USER_IDS)} admin user IDs from environment")
    except ValueError as e:
        print(f"❌ Invalid ADMIN_USER_IDS format: {e}")
        ADMIN_USER_IDS = []
