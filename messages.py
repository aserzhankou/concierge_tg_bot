"""
Message constants for the Telegram bot.
You can create different language versions by copying this file and modifying the strings.
"""

# Error messages
ERR_NOT_SUPERGROUP = "⚠️ Этот бот может работать только в супергруппах. Пожалуйста, преобразуйте группу в супергруппу в настройках."
ERR_CHALLENGE_EXPIRED = "Это задание больше недействительно!"
ERR_CHALLENGE_NOT_FOR_YOU = "Это задание не для вас!"
ERR_INVALID_CALLBACK = "Неверный формат ответа!"
ERR_GENERIC = "Извините, что-то пошло не так!"

# Challenge messages
WELCOME_CHALLENGE = "Добро пожаловать, {user_mention}! Чтобы получить доступ к чату, решите простой вопрос:\n<b>{question}</b>\nУ вас есть 3 минуты."
CHALLENGE_CORRECT = "✅ Все верно! Добро пожаловать в группу {channel_name}, {user_mention}!"
CHALLENGE_WRONG = "❌ Неверный ответ, попробуйте ещё раз!"
CHALLENGE_WRONG_WITH_ATTEMPTS = "❌ Неверный ответ! Осталось попыток: {remaining_attempts}"
CHALLENGE_MAX_ATTEMPTS = "❌ Исчерпано максимальное количество попыток. Пользователь удален из чата."
CHALLENGE_TIMEOUT = "⏰ Время вышло! Пользователь был удален за то, что не решил задание вовремя."
CHALLENGE_EXPIRED_BUTTON = "⚠️ Это задание больше недействительно."

# Debug messages
DEBUG_SIMULATED_JOIN = "Simulating new user join: {user_id}"

# Error handler messages
ERROR_REPORT = """An exception was raised while handling an update
<pre>update = {update}</pre>
<pre>context.chat_data = {chat_data}</pre>
<pre>context.user_data = {user_data}</pre>
<pre>{traceback}</pre>"""

# Startup messages
STARTUP_MESSAGE = "Bot starting up..."
DEBUG_MODE_MESSAGE = "Debug mode: {debug_mode}"
PYTHON_VERSION_MESSAGE = "Python version: {python_version}"
WORKING_DIR_MESSAGE = "Working directory: {working_dir}"
BOT_INIT_MESSAGE = "Initializing bot..."
BOT_INIT_COMPLETE = "Bot initialization complete, starting polling..."

# Log messages
LOG_HANDLERS_SETUP = "Setting up handlers..."
LOG_ERROR_HANDLER_SETUP = "Setting up error handler..."
LOG_CLEANUP_JOB_SETUP = "Setting up cleanup job..."
LOG_DEBUG_MODE = "Running in debug mode"
