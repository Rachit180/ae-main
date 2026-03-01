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
import requests

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
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")

# Optional API key for authentication
API_KEY = os.environ.get("API_KEY", "")

# Auto-send emails on startup (set AUTO_SEND=false to disable)
AUTO_SEND = os.environ.get("AUTO_SEND", "true").lower() == "true"
#har har mahadev

# recipients mapping
recipients = {
"rachitjainemail@gmail.com": ("Kunika Malhotra", "Amazon"),
"markinson2425@gmail.com": ("Mukul Kumar", "Amazon")
}

# Email Body (HTML)
BODY_TEMPLATE = """ 
<html>
<body>
    <p>Hello {hiring_manager},</p>
    <p>My name is Rachit Jain, and I am a final-year B.Tech student in Computer Software Engineering at Delhi Technological University (DTU), formely Delhi College of Engineering (DCE), graduating in 2026. I am writing to express my interest in a full-time Software Development / AI Engineer opportunity at {company_name}.</p>
    <p>I have strong foundations in Data Structures and Algorithms, Object-Oriented Programming, DBMS, Operating Systems, and Computer Networks, complemented by hands-on experience building Agentic AI and GenAI-driven production systems where LLMs and intelligent agents are embedded within backend services for automation, decision orchestration, and real-time inference. My technical skill set includes Java, Python, C++, Spring Boot, React, and Node.js, with a specialization in designing multi-agent architectures, LLM-integrated workflows, and scalable AI-powered platforms.</p>
    <p>During my GenAI Internship at MPS Limited, I designed and built an AI-driven SDLC automation platform that transformed raw requirements into complete software artifacts. The system leveraged LangGraph-based agent orchestration with semantic validation and integrated AI models into a Spring Boot backend to generate user stories, acceptance criteria, sprint plans, architectures, and test cases. The platform incorporated Hugging Face models, GitHub APIs, Apache PDFBox, and Apache POI to deliver structured, version-controlled outputs in a production environment.</p>
    <p>Previously, I have worked across both SDE and AI-focused roles, where I built a machine learning–enabled health-tech application that improved responsiveness and user engagement, and fine-tuned a LLaMA-based conversational AI system to automate customer support workflows and significantly reduce manual effort.</p>
    <p>Beyond internships, I have developed several end-to-end AI systems, including a real-time smart traffic signal optimization system using YOLOv8 and DeepSORT, an automated brain tumor segmentation pipeline using a 3D Attention U-Net, and authored a published research paper on audio-based machine fault diagnosis (ICCCNT 2024).</p>
    <p>I would greatly appreciate the opportunity to contribute to {company_name} and discuss how my experience in Agentic AI, scalable backend systems, and applied machine learning can create meaningful impact for your team.</p>
    <p>Thank you for your time and consideration.</p>


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

def keep_alive_during_wait(delay_secs, service_url):
    """Ping the service every 10 seconds during wait period to prevent spin-down"""
    ping_interval = 10
    elapsed = 0
    
    while elapsed < delay_secs:
        time.sleep(ping_interval)
        elapsed += ping_interval
        try:
            # Self-ping to keep the service alive
            requests.get(service_url, timeout=5)
            logger.debug(f"🔄 Keep-alive ping sent ({elapsed}s / {delay_secs}s)")
        except Exception as e:
            logger.debug(f"⚠️ Keep-alive ping failed: {e}")

def send_emails_async():
    """Send emails in background thread"""
    global sending_status
    
    logger.info("🚀 Starting email sending process...")
    sending_status["is_sending"] = True
    sending_status["results"] = []
    
    # Validate environment variables for HTTPS Mailgun API
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN or not SENDER_ADDRESS:
        error_msg = "Missing required environment variables for HTTPS send: MAILGUN_API_KEY, MAILGUN_DOMAIN, and/or SENDER_ADDRESS"
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

    # Determine service URL for keep-alive pings
    service_url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000/health")
    if not service_url.endswith("/health"):
        service_url = service_url.rstrip("/") + "/health"

    try:
        logger.info(f"🌐 Using Mailgun HTTPS API (domain={MAILGUN_DOMAIN})")
        logger.info(f"📬 Total recipients to send: {len(recipients)}")
        api_base = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        auth = ("api", MAILGUN_API_KEY)
        
        for idx, (recipient, (hiring_manager, company)) in enumerate(recipients.items(), start=1):
            try:
                logger.info(f"📨 [{idx}/{len(recipients)}] Preparing email for {recipient} — {hiring_manager} @ {company}")
                subject = f"Application for SDE Fresher Role - Rachit Jain, DTU at {company}"
                html_body = BODY_TEMPLATE.format(hiring_manager=hiring_manager, company=company)
                
                data = {
                    "from": SENDER_ADDRESS,
                    "to": recipient,
                    "subject": subject,
                    "html": html_body
                }
                
                files = [("attachment", (resume_filename, resume_bytes, "application/pdf"))]
                
                response = requests.post(api_base, auth=auth, data=data, files=files, timeout=60)
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"✅ [{idx}/{len(recipients)}] Successfully sent to {recipient} — {hiring_manager} @ {company}")
                    sending_status["results"].append({
                        "status": "success",
                        "recipient": recipient,
                        "hiring_manager": hiring_manager,
                        "company": company,
                        "index": idx,
                        "total": len(recipients)
                    })
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ [{idx}/{len(recipients)}] Failed to send to {recipient}: {error_msg}")
                    sending_status["results"].append({
                        "status": "error",
                        "recipient": recipient,
                        "error": error_msg
                    })
            
                if idx < len(recipients):
                    delay_secs = random.randint(600, 700)
                    logger.info(f"⏳ Waiting {delay_secs} seconds ({delay_secs//60} minutes) before next email...")
                    logger.info(f"🔄 Keep-alive pings enabled to prevent service spin-down")
                    keep_alive_during_wait(delay_secs, service_url)
            
            except Exception as send_err:
                error_msg = f"Failed to send to {recipient}: {str(send_err)}"
                logger.error(f"❌ [{idx}/{len(recipients)}] {error_msg}")
                sending_status["results"].append({
                    "status": "error",
                    "recipient": recipient,
                    "error": str(send_err)
                })
        
        sending_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"🎉 Email sending completed! Last run: {sending_status['last_run']}")
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

