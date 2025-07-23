import os
import random
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from telegram import Update, ChatPermissions, ChatMember, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler
from telegram.ext import CallbackQueryHandler
from telegram.error import TelegramError
from storage import ChallengeStorage
import traceback
import html
from messages import *  # Import all message constants
from aiohttp import web

try:
    from test_config import DEBUG_MODE, LOG_LEVEL
    debug_mode = DEBUG_MODE
except ImportError:
    debug_mode = False
    LOG_LEVEL = logging.INFO

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        if hasattr(record, 'chat_id'):
            log_data['chat_id'] = record.chat_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'message_id'):
            log_data['message_id'] = record.message_id
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging():
    """Initialize logging configuration"""
    # Create logger first
    logger = logging.getLogger(__name__)
    logger.setLevel(LOG_LEVEL)

    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            print(f"Created logs directory at {log_dir}")
        except Exception as e:
            print(f"Error creating logs directory: {e}")
            raise

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup file handler with rotation
    try:
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'bot.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(LOG_LEVEL)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Error setting up file handler: {e}")
        raise

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(LOG_LEVEL)
    logger.addHandler(console_handler)

    # Setup specific loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    # Setup JSON logging
    try:
        json_handler = RotatingFileHandler(
            os.path.join(log_dir, 'bot_analysis.json'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        json_handler.setFormatter(JsonFormatter())
        json_handler.setLevel(LOG_LEVEL)
        logger.addHandler(json_handler)
        print(f"Logging setup complete. Log files will be written to {log_dir}")
    except Exception as e:
        print(f"Error setting up JSON handler: {e}")
        raise

    return logger

# Initialize logger
logger = setup_logging()

# Log startup information
logger.info(STARTUP_MESSAGE)
logger.info(DEBUG_MODE_MESSAGE.format(debug_mode=debug_mode))
logger.info(PYTHON_VERSION_MESSAGE.format(python_version=os.sys.version))
logger.info(WORKING_DIR_MESSAGE.format(working_dir=os.getcwd()))

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Configuration
MAX_ATTEMPTS = 2  # Maximum number of wrong attempts before kicking user
HTTP_PORT = int(os.getenv('HTTP_PORT', '8080'))  # HTTP server port for healthcheck

# Initialize storage
storage = ChallengeStorage()

# Global variable to track bot health
bot_health = {
    'status': 'starting',
    'start_time': datetime.now(),
    'last_update': datetime.now(),
    'challenges_processed': 0,
    'errors_count': 0
}

async def healthcheck_handler(request):
    """HTTP healthcheck endpoint"""
    uptime = datetime.now() - bot_health['start_time']
    
    health_data = {
        'status': bot_health['status'],
        'uptime_seconds': int(uptime.total_seconds()),
        'start_time': bot_health['start_time'].isoformat(),
        'last_update': bot_health['last_update'].isoformat(),
        'challenges_processed': bot_health['challenges_processed'],
        'errors_count': bot_health['errors_count'],
        'version': '1.0.0'
    }
    
    # Determine HTTP status based on bot health
    if bot_health['status'] == 'running':
        status = 200
    elif bot_health['status'] == 'starting':
        status = 503  # Service Unavailable
    else:
        status = 500  # Internal Server Error
    
    return web.json_response(health_data, status=status)

async def create_http_server():
    """Create and configure the HTTP server"""
    app = web.Application()
    
    # Add healthcheck endpoint
    app.router.add_get('/health', healthcheck_handler)
    app.router.add_get('/healthcheck', healthcheck_handler)  # Alternative endpoint
    
    # Add a simple root endpoint
    async def root_handler(request):
        return web.json_response({
            'service': 'Telegram Bot',
            'status': 'ok',
            'endpoints': ['/health', '/healthcheck']
        })
    
    app.router.add_get('/', root_handler)
    
    return app

def generate_answer_options(correct_answer: int) -> list:
    """Generate 4 options with only one correct answer"""
    options = [correct_answer]
    attempts = 0
    range_offset = 5
    
    while len(options) < 4 and attempts < 50:  # Prevent infinite loop
        wrong_answer = correct_answer + random.randint(-range_offset, range_offset)
        if wrong_answer != correct_answer and wrong_answer not in options and wrong_answer > 0:
            options.append(wrong_answer)
        attempts += 1
        
        if attempts % 10 == 0:  # Expand range if struggling
            range_offset += 5
            
    # If we still don't have enough options, fill with simple increments
    if len(options) < 4:
        for i in range(1, 20):
            if len(options) >= 4:
                break
            candidate = correct_answer + i
            if candidate not in options and candidate > 0:
                options.append(candidate)
            candidate = correct_answer - i
            if len(options) < 4 and candidate not in options and candidate > 0:
                options.append(candidate)
    
    random.shuffle(options)
    return options

async def restrict_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new chat members and member status changes"""
    logger.debug(f"Received update type: {update.message and 'message' or 'chat_member'}")
    
    if update.message and update.message.new_chat_members:
        # Handle new_chat_members update
        for new_member in update.message.new_chat_members:
            if new_member.is_bot:
                continue
            
            user = new_member
            chat_id = update.effective_chat.id
            
            logger.info(f"Processing new member {user.full_name} in chat {chat_id} (from message update)")
            await process_new_member(update, context, chat_id, user)
            
    elif update.chat_member:
        # Handle chat_member update
        chat_member_update = update.chat_member
        old_status = chat_member_update.old_chat_member.status
        new_status = chat_member_update.new_chat_member.status
        user = chat_member_update.new_chat_member.user
        chat_id = update.effective_chat.id

        logger.debug(
            f"Chat member update received:\n"
            f"Chat ID: {chat_id}\n"
            f"User: {user.full_name} (ID: {user.id})\n"
            f"Old status: {old_status}\n"
            f"New status: {new_status}"
        )

        if old_status in ["left", "kicked"] and new_status == "member" and not user.is_bot:
            logger.info(f"Processing new member {user.full_name} in chat {chat_id} (from chat_member update)")
            await process_new_member(update, context, chat_id, user)
        elif new_status in ["left", "kicked"] and not user.is_bot:
            # User left or was kicked, clean up their challenges
            challenges = storage.get_user_challenges(chat_id, user.id)
            for challenge in challenges:
                try:
                    # Delete the challenge message
                    await context.bot.delete_message(
                        chat_id=challenge['chat_id'],
                        message_id=challenge['message_id']
                    )
                except TelegramError as e:
                    logger.warning(
                        f"Could not delete challenge message for leaving user: {str(e)}",
                        extra={
                            'chat_id': chat_id,
                            'user_id': user.id,
                            'message_id': challenge['message_id'],
                            'event_type': 'delete_failed'
                        }
                    )
                storage.remove_challenge(challenge['message_id'])
                logger.info(
                    "Cleaned up challenge for leaving user",
                    extra={
                        'chat_id': chat_id,
                        'user_id': user.id,
                        'message_id': challenge['message_id'],
                        'event_type': 'challenge_cleanup'
                    }
                )
    else:
        logger.warning("Received update without new member information")

async def process_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user):
    """Process a new member joining the chat"""
    try:
        # Update health stats
        bot_health['last_update'] = datetime.now()
        bot_health['challenges_processed'] += 1
        
        # Check if this is a supergroup
        chat = await context.bot.get_chat(chat_id)
        if chat.type != Chat.SUPERGROUP:
            logger.warning(f"Chat {chat_id} is not a supergroup, can't restrict members")
            await context.bot.send_message(
                chat_id,
                ERR_NOT_SUPERGROUP
            )
            return

        # Clean up any existing challenges for this user in this chat
        existing_challenges = storage.get_user_challenges(chat_id, user.id)
        for challenge in existing_challenges:
            try:
                await context.bot.edit_message_text(
                    CHALLENGE_EXPIRED_BUTTON,
                    chat_id=challenge['chat_id'],
                    message_id=challenge['message_id']
                )
            except TelegramError:
                pass
            storage.remove_challenge(challenge['message_id'])
            logger.info(
                "Removed old challenge",
                extra={
                    'chat_id': chat_id,
                    'user_id': user.id,
                    'message_id': challenge['message_id'],
                    'event_type': 'challenge_removed'
                }
            )

        # Restrict user to read-only
        permissions = ChatPermissions(can_send_messages=False)
        await context.bot.restrict_chat_member(chat_id, user.id, permissions=permissions)
        logger.info(
            f"Restricted user {user.full_name}",
            extra={
                'chat_id': chat_id,
                'user_id': user.id,
                'event_type': 'user_restricted'
            }
        )

        # Generate math challenge
        a, b = random.randint(1, 20), random.randint(1, 20)
        correct_answer = a + b
        options = generate_answer_options(correct_answer)
        
        # Create inline keyboard
        keyboard = []
        row = []
        for option in options:
            callback_data = f"answer_{chat_id}_{user.id}_{option}"
            row.append(InlineKeyboardButton(str(option), callback_data=callback_data))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        challenge_text = WELCOME_CHALLENGE.format(
            user_mention=user.mention_html(),
            question=f"{a} + {b} = ?"
        )
        
        sent_message = await context.bot.send_message(
            chat_id, 
            challenge_text, 
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_notification=True
        )
        message_id = sent_message.message_id
        logger.debug(f"Sent challenge message: {message_id}")

        # Store challenge
        storage.add_challenge(
            message_id=message_id,
            chat_id=chat_id,
            user_id=user.id,
            answer=correct_answer
        )

        # Set up a 3-minute timer
        context.job_queue.run_once(
            kick_user_job, 
            180,
            data={'message_id': message_id}
        )
        
        logger.info(f"Set up challenge for user {user.id} with message {message_id}")
    
    except TelegramError as e:
        logger.error(
            f"Error processing new member: {str(e)}",
            extra={
                'chat_id': chat_id,
                'user_id': user.id,
                'event_type': 'error',
                'error_type': type(e).__name__
            },
            exc_info=True
        )

async def handle_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks from challenge answers"""
    query = update.callback_query
    message_id = query.message.message_id
    logger.debug(
        f"Received callback query",
        extra={
            'message_id': message_id,
            'callback_data': query.data,
            'user_id': query.from_user.id,
            'event_type': 'answer_attempt'
        }
    )
    
    try:
        # Get challenge by message_id
        challenge = storage.get_challenge(message_id)
        if not challenge:
            logger.warning(
                f"No challenge found",
                extra={
                    'message_id': message_id,
                    'event_type': 'challenge_not_found'
                }
            )
            await query.answer(ERR_CHALLENGE_EXPIRED, show_alert=True)
            return

        # Parse callback data
        parts = query.data.split('_')
        if len(parts) != 4:
            logger.warning(
                f"Invalid callback data format",
                extra={
                    'callback_data': query.data,
                    'event_type': 'invalid_callback_data'
                }
            )
            await query.answer(ERR_INVALID_CALLBACK, show_alert=True)
            return

        _, chat_id, user_id, answer = parts
        chat_id, user_id, answer = int(chat_id), int(user_id), int(answer)

        # Verify this is the user who should answer
        if query.from_user.id != challenge['user_id']:
            logger.warning(
                f"Wrong user tried to answer",
                extra={
                    'expected_user_id': challenge['user_id'],
                    'actual_user_id': query.from_user.id,
                    'event_type': 'wrong_user_answer'
                }
            )
            await query.answer(ERR_CHALLENGE_NOT_FOR_YOU, show_alert=True)
            return

        logger.debug(
            f"Processing answer",
            extra={
                'user_id': user_id,
                'answer': answer,
                'expected_answer': challenge['answer'],
                'event_type': 'processing_answer'
            }
        )
            
        if answer == challenge['answer']:
            logger.info(
                f"Correct answer received",
                extra={
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'event_type': 'correct_answer'
                }
            )
            # Correct answer - unrestrict user
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
            await context.bot.restrict_chat_member(chat_id, user_id, permissions=permissions)
            
            # Update challenge message to welcome message
            await context.bot.edit_message_text(
                CHALLENGE_CORRECT.format(
                    user_mention=query.from_user.mention_html(),
                    channel_name=query.message.chat.title
                ),
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML"
            )
            
            # Schedule deletion of welcome message after 3 minutes
            context.job_queue.run_once(
                delete_welcome_message_job,
                180,
                data={'message_id': message_id, 'chat_id': chat_id}
            )
            
            # Cleanup
            storage.remove_challenge(message_id)
            # No personal popup - only welcome message in chat
        else:
            logger.info(
                f"Wrong answer received",
                extra={
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'answer': answer,
                    'expected_answer': challenge['answer'],
                    'event_type': 'wrong_answer'
                }
            )
            
            # Increment attempt count
            attempts = storage.increment_attempts(message_id)
            remaining_attempts = MAX_ATTEMPTS - attempts
            
            logger.info(
                f"User attempt count updated",
                extra={
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'attempts': attempts,
                    'remaining_attempts': remaining_attempts,
                    'event_type': 'attempt_incremented'
                }
            )
            
            if attempts >= MAX_ATTEMPTS:
                # Max attempts reached - kick user
                await kick_user_max_attempts(context, chat_id, user_id, message_id)
                await query.answer(CHALLENGE_MAX_ATTEMPTS, show_alert=True)
            else:
                # Still have attempts left
                if remaining_attempts > 0:
                    await query.answer(
                        CHALLENGE_WRONG_WITH_ATTEMPTS.format(remaining_attempts=remaining_attempts), 
                        show_alert=True
                    )
                else:
                    await query.answer(CHALLENGE_WRONG, show_alert=True)
            
    except (ValueError, KeyError) as e:
        logger.error(
            f"Error handling answer: {str(e)}",
            extra={
                'message_id': message_id,
                'event_type': 'error',
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        await query.answer(ERR_GENERIC, show_alert=True)
    except TelegramError as e:
        logger.error(
            f"Telegram error: {str(e)}",
            extra={
                'message_id': message_id,
                'event_type': 'telegram_error',
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        await query.answer(ERR_GENERIC, show_alert=True)

async def kick_user_job(context: ContextTypes.DEFAULT_TYPE):
    """Handle timeout for challenge"""
    message_id = context.job.data['message_id']
    
    try:
        challenge = storage.get_challenge(message_id)
        if not challenge:
            return

        # First kick the user with proper error handling
        try:
            await context.bot.ban_chat_member(challenge['chat_id'], challenge['user_id'])
            await context.bot.unban_chat_member(challenge['chat_id'], challenge['user_id'])
            logger.info(
                "User kicked due to timeout",
                extra={
                    'chat_id': challenge['chat_id'],
                    'user_id': challenge['user_id'],
                    'message_id': message_id,
                    'event_type': 'challenge_timeout'
                }
            )
        except TelegramError as e:
            logger.error(
                f"Failed to kick user: {str(e)}",
                extra={
                    'chat_id': challenge['chat_id'],
                    'user_id': challenge['user_id'],
                    'message_id': message_id,
                    'event_type': 'kick_failed',
                    'error_type': type(e).__name__
                }
            )
            # Don't proceed with cleanup if kick failed
            return
        
        # Then delete the challenge message
        try:
            await context.bot.delete_message(
                chat_id=challenge['chat_id'],
                message_id=challenge['message_id']
            )
        except TelegramError as e:
            logger.warning(
                f"Could not delete challenge message: {str(e)}",
                extra={
                    'chat_id': challenge['chat_id'],
                    'message_id': message_id,
                    'event_type': 'delete_failed'
                }
            )
        
        storage.remove_challenge(message_id)
        
    except Exception as e:
        logger.error(
            f"Unexpected error in kick job: {str(e)}",
            extra={
                'message_id': message_id,
                'event_type': 'kick_error',
                'error_type': type(e).__name__
            },
            exc_info=True
        )

async def kick_user_max_attempts(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, message_id: int):
    """Kick user when max attempts reached and cleanup challenge"""
    try:
        # First kick the user
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id)
        
        # Update message to show max attempts reached
        try:
            await context.bot.edit_message_text(
                CHALLENGE_MAX_ATTEMPTS,
                chat_id=chat_id,
                message_id=message_id
            )
            
            # Schedule deletion of the failure message after 10 seconds
            context.job_queue.run_once(
                delete_welcome_message_job,
                10,
                data={'message_id': message_id, 'chat_id': chat_id}
            )
        except TelegramError as e:
            logger.warning(
                f"Could not update challenge message: {str(e)}",
                extra={
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'event_type': 'update_failed'
                }
            )
        
        # Remove challenge from storage
        storage.remove_challenge(message_id)
        
        logger.info(
            "User kicked due to max attempts",
            extra={
                'chat_id': chat_id,
                'user_id': user_id,
                'message_id': message_id,
                'event_type': 'max_attempts_kick'
            }
        )
    except TelegramError as e:
        logger.error(
            f"Error kicking user for max attempts: {str(e)}",
            extra={
                'chat_id': chat_id,
                'user_id': user_id,
                'message_id': message_id,
                'event_type': 'kick_max_attempts_error',
                'error_type': type(e).__name__
            },
            exc_info=True
        )

async def delete_welcome_message_job(context: ContextTypes.DEFAULT_TYPE):
    """Delete welcome message after 3 minutes"""
    message_id = context.job.data['message_id']
    chat_id = context.job.data['chat_id']
    
    try:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
        logger.info(
            "Deleted welcome message after timeout",
            extra={
                'chat_id': chat_id,
                'message_id': message_id,
                'event_type': 'welcome_message_deleted'
            }
        )
    except TelegramError as e:
        logger.warning(
            f"Could not delete welcome message: {str(e)}",
            extra={
                'chat_id': chat_id,
                'message_id': message_id,
                'event_type': 'delete_welcome_failed'
            }
        )

async def cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    """Periodic cleanup of expired challenges"""
    storage.cleanup_expired()

# Add debug commands if in debug mode
async def debug_simulate_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to simulate user join"""
    if not debug_mode:
        return
        
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    logger.info(DEBUG_SIMULATED_JOIN.format(user_id=user_id))
    
    # Create mock member update
    mock_update = Update(
        update.update_id,
        chat_member=ChatMemberUpdated(
            chat=update.effective_chat,
            from_user=update.effective_user,
            date=update.message.date,
            old_chat_member=ChatMember(user=update.effective_user, status="left"),
            new_chat_member=ChatMember(user=update.effective_user, status="member"),
        )
    )
    
    await restrict_new_member(mock_update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Update error count
    bot_health['errors_count'] += 1
    bot_health['last_update'] = datetime.now()
    
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Get the error traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = ERROR_REPORT.format(
        update=html.escape(json.dumps(update_str, indent=2, ensure_ascii=False)),
        chat_data=html.escape(str(context.chat_data)),
        user_data=html.escape(str(context.user_data)),
        traceback=html.escape(tb_string)
    )

    logger.error(
        "Exception occurred",
        extra={
            'update': update_str,
            'error': str(context.error),
            'traceback': tb_string,
            'event_type': 'exception'
        }
    )

async def start_http_server():
    """Start the HTTP server"""
    app = await create_http_server()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', HTTP_PORT)
    await site.start()
    
    logger.info(f"HTTP server started on port {HTTP_PORT}")
    logger.info(f"Healthcheck available at: http://localhost:{HTTP_PORT}/health")
    
    return runner

def main():
    try:
        logger.info(BOT_INIT_MESSAGE)
        
        # Create the bot application
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add handlers
        logger.debug(LOG_HANDLERS_SETUP)
        app.add_handler(ChatMemberHandler(restrict_new_member, ChatMemberHandler.CHAT_MEMBER))
        app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS, restrict_new_member))
        app.add_handler(CallbackQueryHandler(handle_answer_callback, pattern=r"^answer_"))
        
        # Add error handler
        logger.debug(LOG_ERROR_HANDLER_SETUP)
        app.add_error_handler(error_handler)
        
        # Add periodic cleanup job
        logger.debug(LOG_CLEANUP_JOB_SETUP)
        app.job_queue.run_repeating(cleanup_job, interval=60)  # Run every minute
        
        if debug_mode:
            logger.info(LOG_DEBUG_MODE)
            app.add_handler(CommandHandler('debug_join', debug_simulate_join))
        
        # Global variable to store HTTP runner
        http_runner = None
        
        async def post_init(application):
            """Initialize HTTP server after bot initialization"""
            nonlocal http_runner
            try:
                http_runner = await start_http_server()
                bot_health['status'] = 'running'
                bot_health['last_update'] = datetime.now()
                logger.info("Bot and HTTP server initialization complete")
            except Exception as e:
                logger.error(f"Failed to start HTTP server: {e}")
                bot_health['status'] = 'error'
                raise
        
        async def post_stop(application):
            """Cleanup HTTP server when bot stops"""
            nonlocal http_runner
            if http_runner:
                try:
                    logger.info("Shutting down HTTP server...")
                    bot_health['status'] = 'stopping'
                    await http_runner.cleanup()
                    logger.info("HTTP server shutdown complete")
                except Exception as e:
                    logger.error(f"Error during HTTP server shutdown: {e}")
        
        # Set up lifecycle hooks
        app.post_init = post_init
        app.post_stop = post_stop
        
        logger.info(BOT_INIT_COMPLETE)
        
        # Run the bot (this handles the event loop properly)
        app.run_polling(
            allowed_updates=[
                Update.MESSAGE,
                Update.CHAT_MEMBER,
                Update.MY_CHAT_MEMBER,
                Update.CALLBACK_QUERY
            ],
            drop_pending_updates=True
        )
        
    except Exception as e:
        bot_health['status'] = 'error'
        bot_health['errors_count'] += 1
        logger.critical(
            "Fatal error during bot startup",
            extra={
                'error': str(e),
                'traceback': traceback.format_exc(),
                'event_type': 'startup_error'
            },
            exc_info=True
        )
        raise

if __name__ == '__main__':
    main() 