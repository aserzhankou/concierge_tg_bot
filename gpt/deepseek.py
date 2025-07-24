"""
DeepSeek API integration for spam detection
"""
import asyncio
import logging

# Import configuration
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    SPAM_DETECTION_ENABLED, SPAM_DETECTION_PROMPT
)

logger = logging.getLogger(__name__)

# DeepSeek for spam detection (uses OpenAI-compatible package)
try:
    import openai
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

# Initialize DeepSeek client (will be validated during startup)
deepseek_client = None


async def test_deepseek_connection() -> bool:
    """Test DeepSeek API connection and validate API key"""
    if not DEEPSEEK_AVAILABLE:
        logger.info("OpenAI package not installed - spam detection disabled")
        return False
    
    if not DEEPSEEK_API_KEY:
        logger.info("DEEPSEEK_API_KEY not set - spam detection disabled")
        return False
    
    if not SPAM_DETECTION_ENABLED:
        logger.info("Spam detection disabled in configuration")
        return False
    
    try:
        # Initialize DeepSeek client (using OpenAI-compatible interface)
        test_client = openai.OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        
        logger.info("Testing DeepSeek API connection...")
        
        # Test with a simple completion request
        logger.debug("🤖 Testing DeepSeek API with test request...")
        response = await asyncio.to_thread(
            test_client.chat.completions.create,
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a test system."},
                {"role": "user", "content": "Respond with exactly: TEST"}
            ],
            max_tokens=5,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip()
        logger.debug(f"🤖 DeepSeek test response: '{result}'")
        logger.debug(f"🤖 Test tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
        
        if "TEST" in result.upper():
            logger.info("✅ DeepSeek API connection successful - spam detection enabled")
            global deepseek_client
            deepseek_client = test_client
            return True
        else:
            logger.warning(f"❌ DeepSeek API test failed - unexpected response: {result}")
            return False
            
    except openai.AuthenticationError:
        logger.error("❌ DeepSeek API authentication failed - invalid API key")
        logger.error("Please check your DEEPSEEK_API_KEY environment variable")
        return False
    except openai.RateLimitError:
        logger.warning("⚠️ DeepSeek API rate limit exceeded - will retry later")
        logger.warning("Spam detection temporarily disabled")
        return False
    except openai.APIError as e:
        logger.error(f"❌ DeepSeek API error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error testing DeepSeek connection: {str(e)}")
        return False


async def detect_spam_with_deepseek(message_text: str) -> bool:
    """Use DeepSeek to detect if a message is spam/advertisement"""
    if not deepseek_client:
        return False  # If DeepSeek not available, assume not spam

    try:
        prompt = SPAM_DETECTION_PROMPT.format(message=message_text)
        
        # Log the request details
        logger.debug(f"🤖 DeepSeek API Request:")
        logger.debug(f"  Model: {DEEPSEEK_MODEL}")
        logger.debug(f"  System prompt: Ты система определения спама для Telegram чатов.")
        logger.debug(f"  User prompt: {prompt}")
        logger.debug(f"  Message to analyze: '{message_text}'")
        logger.debug(f"  Max tokens: 10, Temperature: 0.1")

        response = await asyncio.to_thread(
            deepseek_client.chat.completions.create,
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "Ты система определения спама для Telegram чатов."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.1
        )

        # Log the response details
        result = response.choices[0].message.content.strip()
        is_spam = "SPAM" in result.upper()
        
        logger.debug(f"🤖 DeepSeek API Response:")
        logger.debug(f"  Raw response: '{result}'")
        logger.debug(f"  Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
        logger.debug(f"  Prompt tokens: {response.usage.prompt_tokens if response.usage else 'N/A'}")
        logger.debug(f"  Completion tokens: {response.usage.completion_tokens if response.usage else 'N/A'}")
        logger.debug(f"  Finish reason: {response.choices[0].finish_reason}")
        logger.debug(f"  Spam detected: {is_spam}")

        logger.info(f"Spam detection result: '{result}' -> {'SPAM' if is_spam else 'SAFE'} "
                   f"for message: '{message_text[:50]}{'...' if len(message_text) > 50 else ''}'")
        return is_spam

    except Exception as e:
        logger.error(f"Error in DeepSeek spam detection: {str(e)}")
        logger.debug(f"Failed message was: '{message_text}'")
        return False  # If error, assume not spam to avoid false positives


def is_deepseek_available() -> bool:
    """Check if DeepSeek client is available and configured"""
    return deepseek_client is not None


async def initialize_deepseek():
    """Initialize DeepSeek during startup"""
    import messages
    logger.info(messages.DEEPSEEK_CHECK_MESSAGE)
    deepseek_status = await test_deepseek_connection()
    
    if deepseek_status:
        logger.info("🤖 AI-powered spam detection is active")
    else:
        logger.info("📝 Basic protection mode (no AI spam detection)")
    
    return deepseek_status 