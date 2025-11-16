#!/usr/bin/env python3
"""
Test Mailgun SMTP connection without sending emails
"""

import smtplib
import os

# Try to load .env file if it exists (for local development)
def load_env_file():
    """Load .env file if it exists (simple parser, no external deps)"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.isfile(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Only set if not already in environment
                    if key and key not in os.environ:
                        os.environ[key] = value

load_env_file()

# Load from environment
MAILGUN_SMTP_LOGIN = os.environ.get("MAILGUN_SMTP_LOGIN")
MAILGUN_SMTP_PASSWORD = os.environ.get("MAILGUN_SMTP_PASSWORD")
MAILGUN_SMTP_HOST = os.environ.get("MAILGUN_SMTP_HOST", "smtp.mailgun.org")
MAILGUN_SMTP_PORT = int(os.environ.get("MAILGUN_SMTP_PORT", "587"))

def test_connection():
    print("🔍 Testing Mailgun SMTP connection...")
    print(f"   Host: {MAILGUN_SMTP_HOST}")
    print(f"   Port: {MAILGUN_SMTP_PORT}")
    print(f"   Login: {MAILGUN_SMTP_LOGIN}")
    print()
    
    if not MAILGUN_SMTP_LOGIN or not MAILGUN_SMTP_PASSWORD:
        print("❌ Missing environment variables:")
        if not MAILGUN_SMTP_LOGIN:
            print("   - MAILGUN_SMTP_LOGIN")
        if not MAILGUN_SMTP_PASSWORD:
            print("   - MAILGUN_SMTP_PASSWORD")
        print("\nPlease set these environment variables and try again.")
        return False
    
    try:
        print("📧 Connecting to Mailgun SMTP...")
        server = smtplib.SMTP(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT, timeout=30)
        server.set_debuglevel(0)  # Set to 1 for verbose output
        server.ehlo()
        
        print("🔒 Starting TLS...")
        if MAILGUN_SMTP_PORT == 587:
            server.starttls()
            server.ehlo()
        
        print("🔑 Logging in...")
        server.login(MAILGUN_SMTP_LOGIN, MAILGUN_SMTP_PASSWORD)
        
        print("✅ SUCCESS! Connection established successfully.")
        print("   You can now use send_email.py to send emails.")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("❌ AUTHENTICATION FAILED")
        print(f"   Error: {e}")
        print("\nPlease check:")
        print("   1. Your MAILGUN_SMTP_LOGIN is correct")
        print("   2. Your MAILGUN_SMTP_PASSWORD is correct")
        print("   3. Your Mailgun domain is verified")
        return False
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print("\nPlease check:")
        print("   1. Your internet connection")
        print("   2. MAILGUN_SMTP_HOST and MAILGUN_SMTP_PORT settings")
        print("   3. Firewall settings")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)

