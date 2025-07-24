#!/usr/bin/env python3
"""
Emergency script to clear Telegram webhook that might be causing conflicts.
Run this if you're getting persistent conflict errors.
"""

import os
import requests
import sys
from config import BOT_TOKEN

def clear_webhook():
    """Clear any existing webhook for the bot"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in config")
        return False
    
    # Delete webhook
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    
    try:
        print("🔄 Clearing webhook...")
        response = requests.post(url, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook cleared successfully")
            print(f"   Description: {result.get('description', 'No description')}")
            return True
        else:
            print(f"❌ Failed to clear webhook: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing webhook: {e}")
        return False

def get_webhook_info():
    """Get current webhook information"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            info = result['result']
            print("📋 Current webhook info:")
            print(f"   URL: {info.get('url', 'None')}")
            print(f"   Has custom certificate: {info.get('has_custom_certificate', False)}")
            print(f"   Pending updates: {info.get('pending_update_count', 0)}")
            print(f"   Last error: {info.get('last_error_message', 'None')}")
            return info
        else:
            print(f"❌ Failed to get webhook info: {result.get('description', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting webhook info: {e}")
        return None

if __name__ == '__main__':
    print("🚨 Telegram Webhook Emergency Cleanup")
    print("=====================================")
    
    # Get current webhook info
    webhook_info = get_webhook_info()
    
    if webhook_info and webhook_info.get('url'):
        print(f"\n⚠️  Webhook is set to: {webhook_info['url']}")
        confirm = input("Do you want to clear it? (y/N): ").lower().strip()
        
        if confirm == 'y':
            if clear_webhook():
                print("\n✅ Webhook cleared! You can now deploy your bot with polling.")
                print("💡 Wait 30-60 seconds before redeploying to ensure cleanup.")
            else:
                print("\n❌ Failed to clear webhook. Check your bot token.")
                sys.exit(1)
        else:
            print("❌ Webhook not cleared.")
    else:
        print("\n✅ No webhook is currently set. Conflicts might be from multiple polling instances.")
        print("💡 Make sure only one instance of your bot is running.")
    
    print("\n🎯 Next steps:")
    print("1. Wait 30-60 seconds")
    print("2. Deploy your bot using start.py")
    print("3. Ensure only ONE instance is running on Render") 