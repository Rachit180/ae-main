#!/usr/bin/env python3
# Har Har Mahadev
# Flask Web Service for Email Sender

import smtplib
import time
import random
import os
import logging
from flask import Flask, jsonify, request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Try to load .env file if it exists (for local development)
def load_env_file():
    """Load .env file if it exists (simple parser, no external deps)"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.isfile(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value

load_env_file()

# === CONFIGURE FROM ENVIRONMENT ===
MAILGUN_SMTP_LOGIN = os.environ.get("MAILGUN_SMTP_LOGIN")
MAILGUN_SMTP_PASSWORD = os.environ.get("MAILGUN_SMTP_PASSWORD")
MAILGUN_SMTP_HOST = os.environ.get("MAILGUN_SMTP_HOST", "smtp.mailgun.org")
MAILGUN_SMTP_PORT = int(os.environ.get("MAILGUN_SMTP_PORT", "587"))
SENDER_ADDRESS = os.environ.get("SENDER_ADDRESS", MAILGUN_SMTP_LOGIN)
RESUME_FILE = os.environ.get("RESUME_FILE", "RACHITJAIN_RESUME.pdf")

# Optional API key for authentication
API_KEY = os.environ.get("API_KEY", "")

# Auto-send emails on startup (set AUTO_SEND=false to disable)
AUTO_SEND = os.environ.get("AUTO_SEND", "true").lower() == "true"

# recipients mapping
recipients = {
   

"ojas.mittal@iongroup.com": ("Ojas Mittal", "ION"),
"shantanu.bhardwaj@iongroup.com": ("Shantanu Bhardwaj", "ION"),
}

# Email Body (HTML)
BODY_TEMPLATE = """
<html>
<body>
    <p>Hello <b>{hiring_manager}</b>,</p>

    <p>My name is <b>Rachit Jain</b>. I am a <b>fourth-year B.Tech (Software Engineering) student</b> at
    <b>Delhi Technological University</b> (2022–2026), with a strong foundation in software development and machine learning.
    I am proficient in <b>C / C++ , Python, Node.js, React, OpenCV, TensorFlow, PyTorch,</b> and have hands-on experience
    across full-stack development and AI/ML pipelines. I am seeking a <b>full-time fresher opportunity</b> in SDE, ML engineering,
    or a related domain.</p>

    <p>Below are a few highlights from my recent work and internships:</p>

    <ul>
        <li><b>AI Intern — Path Infotech Ltd (Jun 2025 – Jul 2025):</b> Fine-tuned Llama 3 and built a high-performance conversational chatbot to automate AC product-defect support, improving response times and reducing manual effort.</li>

        <li><b>Full Stack Developer — Gabbit Trans Systems (Jun 2024 – Jul 2024):</b> Built core features for a health app (Android/Flutter + Node.js backend), improving responsiveness and user engagement.</li>

        <li><b>Bharat Bhraman (AI travel platform):</b> Designed an AI-driven itinerary & image-to-place recommendation system (CLIP + ONNX, TF-IDF + cosine + geo fusion) with real-time suggestions and smart guide matchmaking.</li>

        <li><b>Dehaze Rescue Vision:</b> Built a real-time de-smoking / de-hazing pipeline using YOLOv8, Dark Channel Prior, and STTN to improve rescue-scene visibility and tracking.</li>

        <li><b>Research — Audio-based Machine Fault Diagnosis (Published):</b> Developed a hybrid feature-extraction + ensemble learning pipeline (SVC, XGBoost, Random Forest) achieving high detection accuracy.</li>

    </ul>

    <p>I am confident my combination of full-stack and ML experience — plus published research and hands-on internships — will allow me to contribute effectively to your team.</p>

    <p>I would be grateful if you consider my application for relevant roles at your firm. Thank you for your time and consideration.</p>

    <p>Yours sincerely,<br>
    <b>Rachit Jain</b><br>
    📧 <a href="mailto:rachitjainemail@gmail.com">rachitjainemail@gmail.com</a><br>
    📞 +91-9650090580<br>
    <a href="https://github.com/Rachit180">GitHub</a> | 
    <a href="https://www.linkedin.com/in/rachit-jain-875aa2247/">LinkedIn</a></p>

    <p style="font-size:0.9em; color:gray;">
        (Resume details and full project list are available in my resume.)
    </p>

</body>
</html>
"""

# Global status tracking
sending_status = {
    "is_sending": False,
    "last_run": None,
    "results": []
}

def build_message(sender, recipient, hiring_manager, company, resume_bytes, resume_filename):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = f"Application for SDE Fresher Role - Rachit Jain, DTU at {company}"
    body = BODY_TEMPLATE.format(hiring_manager=hiring_manager, company=company)
    msg.attach(MIMEText(body, "html"))

    resume = MIMEApplication(resume_bytes, _subtype="pdf")
    resume.add_header("Content-Disposition", f'attachment; filename="{resume_filename}"')
    msg.attach(resume)
    return msg

def send_emails_async():
    """Send emails in background thread"""
    global sending_status
    
    logger.info("🚀 Starting email sending process...")
    sending_status["is_sending"] = True
    sending_status["results"] = []
    
    # Validate environment variables
    if not MAILGUN_SMTP_LOGIN or not MAILGUN_SMTP_PASSWORD:
        error_msg = "Missing required environment variables: MAILGUN_SMTP_LOGIN and/or MAILGUN_SMTP_PASSWORD"
        logger.error(f"❌ {error_msg}")
        sending_status["results"].append({
            "status": "error",
            "message": error_msg
        })
        sending_status["is_sending"] = False
        return
    
    if not os.path.isfile(RESUME_FILE):
        error_msg = f"Resume file not found at: {RESUME_FILE}"
        logger.error(f"❌ {error_msg}")
        sending_status["results"].append({
            "status": "error",
            "message": error_msg
        })
        sending_status["is_sending"] = False
        return

    logger.info(f"📄 Reading resume file: {RESUME_FILE}")
    with open(RESUME_FILE, "rb") as f:
        resume_bytes = f.read()
    resume_filename = os.path.basename(RESUME_FILE)
    logger.info(f"✅ Resume file loaded: {len(resume_bytes)} bytes")

    # Try connecting with retries and different methods
    max_retries = 3
    server = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"📧 Attempt {attempt}/{max_retries}: Connecting to Mailgun SMTP ({MAILGUN_SMTP_HOST}:{MAILGUN_SMTP_PORT})...")
            
            # Try different connection methods
            if MAILGUN_SMTP_PORT == 465:
                # SSL connection
                logger.info("🔒 Using SSL connection (port 465)")
                server = smtplib.SMTP_SSL(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT, timeout=60)
            elif MAILGUN_SMTP_PORT == 587:
                # STARTTLS connection
                logger.info("🔒 Using STARTTLS connection (port 587)")
                server = smtplib.SMTP(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT, timeout=60)
                server.set_debuglevel(0)
                server.ehlo()
                server.starttls()
                server.ehlo()
            elif MAILGUN_SMTP_PORT == 2525:
                # Alternative port with STARTTLS
                logger.info("🔒 Using STARTTLS connection (port 2525)")
                server = smtplib.SMTP(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT, timeout=60)
                server.set_debuglevel(0)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                # Default connection
                logger.info("🔒 Using default connection")
                server = smtplib.SMTP(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT, timeout=60)
                server.ehlo()
            
            logger.info("🔑 Attempting to login...")
            server.login(MAILGUN_SMTP_LOGIN, MAILGUN_SMTP_PASSWORD)
            logger.info("✅ Successfully connected and authenticated to Mailgun SMTP")
            break  # Success, exit retry loop
            
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, OSError, TimeoutError) as conn_err:
            if attempt < max_retries:
                wait_time = attempt * 5  # Exponential backoff: 5s, 10s, 15s
                logger.warning(f"⚠️ Connection attempt {attempt} failed: {str(conn_err)}")
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                if server:
                    try:
                        server.quit()
                    except:
                        pass
                    server = None
            else:
                # Try alternative port on last attempt
                if MAILGUN_SMTP_PORT == 587:
                    logger.info("🔄 Trying alternative port 2525...")
                    try:
                        server = smtplib.SMTP(MAILGUN_SMTP_HOST, 2525, timeout=60)
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(MAILGUN_SMTP_LOGIN, MAILGUN_SMTP_PASSWORD)
                        logger.info("✅ Successfully connected using alternative port 2525")
                        break
                    except Exception as alt_err:
                        logger.error(f"❌ Alternative port also failed: {str(alt_err)}")
                        raise conn_err
                else:
                    raise conn_err
        except Exception as e:
            logger.error(f"❌ Connection error: {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 5
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
    
    if not server:
        raise Exception("Failed to establish SMTP connection after all retries")
    
    try:
        logger.info(f"📬 Total recipients to send: {len(recipients)}")
        
        for idx, (recipient, (hiring_manager, company)) in enumerate(recipients.items(), start=1):
            try:
                logger.info(f"📨 [{idx}/{len(recipients)}] Preparing email for {recipient} — {hiring_manager} @ {company}")
                msg = build_message(SENDER_ADDRESS, recipient, hiring_manager, company, resume_bytes, resume_filename)
                server.sendmail(SENDER_ADDRESS, recipient, msg.as_string())
                logger.info(f"✅ [{idx}/{len(recipients)}] Successfully sent to {recipient} — {hiring_manager} @ {company}")
                sending_status["results"].append({
                    "status": "success",
                    "recipient": recipient,
                    "hiring_manager": hiring_manager,
                    "company": company,
                    "index": idx,
                    "total": len(recipients)
                })
            except Exception as send_err:
                error_msg = f"Failed to send to {recipient}: {str(send_err)}"
                logger.error(f"❌ [{idx}/{len(recipients)}] {error_msg}")
                sending_status["results"].append({
                    "status": "error",
                    "recipient": recipient,
                    "error": str(send_err)
                })

            if idx < len(recipients):
                delay_secs = random.randint(60, 70)
                logger.info(f"⏳ Waiting {delay_secs} seconds ({delay_secs//60} minutes) before next email...")
                time.sleep(delay_secs)

        if server:
            server.quit()
            logger.info("🔌 SMTP connection closed")
        sending_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"🎉 Email sending completed! Last run: {sending_status['last_run']}")
        
    except Exception as e:
        error_msg = f"Failed to connect/login to Mailgun SMTP: {str(e)}"
        logger.error(f"❌ {error_msg}")
        sending_status["results"].append({
            "status": "error",
            "message": error_msg
        })
        if server:
            try:
                server.quit()
            except:
                pass
    finally:
        sending_status["is_sending"] = False
        logger.info("🏁 Email sending process finished")

def check_auth():
    """Check API key if configured"""
    if API_KEY:
        provided_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if provided_key != API_KEY:
            return False
    return True

@app.route("/")
def home():
    return jsonify({
        "service": "Email Sender API",
        "status": "running",
        "endpoints": {
            "/": "This page",
            "/health": "Health check",
            "/send": "Trigger email sending (POST)",
            "/status": "Check sending status (GET)"
        }
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "mailgun_configured": bool(MAILGUN_SMTP_LOGIN and MAILGUN_SMTP_PASSWORD),
        "resume_file_exists": os.path.isfile(RESUME_FILE),
        "recipients_count": len(recipients)
    })

@app.route("/send", methods=["POST"])
def send_emails():
    if not check_auth():
        logger.warning("⚠️ Unauthorized access attempt to /send endpoint")
        return jsonify({"error": "Unauthorized"}), 401
    
    if sending_status["is_sending"]:
        logger.warning("⚠️ Email sending already in progress, request rejected")
        return jsonify({
            "status": "busy",
            "message": "Email sending is already in progress"
        }), 409
    
    logger.info(f"📬 Email sending triggered via API. Recipients: {len(recipients)}")
    # Start sending in background thread
    thread = threading.Thread(target=send_emails_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": "Email sending started in background",
        "recipients_count": len(recipients)
    })

@app.route("/status", methods=["GET"])
def get_status():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({
        "is_sending": sending_status["is_sending"],
        "last_run": sending_status["last_run"],
        "results": sending_status["results"],
        "total_recipients": len(recipients)
    })

def trigger_auto_send():
    """Trigger email sending automatically after a short delay"""
    # Wait 5 seconds for the server to fully start
    time.sleep(5)
    
    if not AUTO_SEND:
        logger.info("⏸️  Auto-send disabled. Set AUTO_SEND=true to enable automatic sending.")
        return
    
    if sending_status["is_sending"]:
        logger.info("⏭️  Skipping auto-send - email sending already in progress")
        return
    
    # Check if emails were already sent in this session (prevent duplicate sends on quick restarts)
    if sending_status["last_run"]:
        logger.info(f"⏭️  Skipping auto-send - emails already sent on {sending_status['last_run']}")
        logger.info("💡 To send again, use POST /send endpoint or redeploy the service")
        return
    
    logger.info("🤖 Auto-send enabled: Starting email sending automatically...")
    logger.info(f"📬 Will send to {len(recipients)} recipient(s)")
    thread = threading.Thread(target=send_emails_async)
    thread.daemon = True
    thread.start()

# Start auto-send in background when app initializes
if AUTO_SEND:
    startup_thread = threading.Thread(target=trigger_auto_send)
    startup_thread.daemon = True
    startup_thread.start()
    logger.info("✅ Auto-send thread started - emails will be sent automatically on startup")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

