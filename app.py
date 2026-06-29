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

# === TARGET MARKET ===
# Set to "india" (or "1") for India recipients.
# Set to "us" (or "2") for US recipients.
# Controls which resume is attached and which email body is used.
TARGET_MARKET = "us"   # <-- change to "us" when targeting US companies

_market = TARGET_MARKET.strip().lower()
if _market in ("us", "2"):
    RESUME_FILE_OVERRIDE = os.path.join(os.path.dirname(__file__), "RACHITJAIN_RESUME1.pdf")
    MARKET = "us"
else:
    RESUME_FILE_OVERRIDE = os.path.join(os.path.dirname(__file__), "RACHITJAIN_RESUME.pdf")
    MARKET = "india"

# === APPLICATION NUMBER ===
# Set this before running the script. The SAME number is sent to ALL recipients.
# Leave empty ("") to omit the application number from the email entirely.
APPLICATION_NUMBER = ""

# recipients mapping
recipients = {
    "jlu@zoox.com": ("Julian L", "Zoox"),
    "amoraros@zoox.com": ("Alex M", "Zoox"),
    "mrudolph@zoox.com": ("Matt R", "Zoox"),
    "mitchell@zoox.com": ("Mitchell F", "Zoox"),
    "jdhaliwal@zoox.com": ("Jeetha D", "Zoox"),
    "x-aisacsson@zoox.com": ("Ashley I", "Zoox"),
    "awong@zoox.com": ("Alicia W", "Zoox"),
    "x-rventon@zoox.com": ("Ratidzo V", "Zoox"),
    "zewang@zoox.com": ("Zeyu W", "Zoox"),
    "jkwong@zoox.com": ("Jessica K", "Zoox"),
    "yzhang@zoox.com": ("Yu Z", "Zoox"),
    "bfeig@zoox.com": ("Brandon F", "Zoox"),
    "dcruz@zoox.com": ("David C", "Zoox"),
    "ebogner@zoox.com": ("Emily Bogner", "Zoox"),
    "x-jchoksi@zoox.com": ("Jeet C", "Zoox"),
    "cseto@zoox.com": ("Christopher S", "Zoox"),
    "findaheng@zoox.com": ("Francis I", "Zoox"),
    "kmoyer@zoox.com": ("Kathryn M", "Zoox"),
    "mmehrotra@zoox.com": ("Mansi M", "Zoox"),
    "ebeiers@zoox.com": ("Emily B", "Zoox"),
    "byackabonis@zoox.com": ("Bill Y", "Zoox"),
    "mrganesina@zoox.com": ("Meghana G", "Zoox"),
    "sseddon@zoox.com": ("Selena S", "Zoox"),
    "cjack@zoox.com": ("Christopher Jack", "Zoox"),
    "ts@zoox.com": ("Tulasi Siddhartha", "Zoox"),
    "smishra@zoox.com": ("Sambit M", "Zoox"),
    "cdunn@zoox.com": ("Colleen D", "Zoox"),
    "qmauga@zoox.com": ("Quirisa M", "Zoox"),
    "gpatnashetty@zoox.com": ("Gaurav P", "Zoox"),
    "jsan@zoox.com": ("Jonny S", "Zoox"),
    "tnash@zoox.com": ("Taylor N", "Zoox"),
    "sshah@zoox.com": ("Sanket S", "Zoox"),
    "jbowman@zoox.com": ("Jay Bowman", "Zoox"),
    "x-modmartinez@zoox.com": ("Modesto M", "Zoox"),
    "rpecina@zoox.com": ("Ricardo P", "Zoox")
}


def get_email_body(hiring_manager, company):
    """Build the HTML email body based on TARGET_MARKET."""
    app_number_section = ""
    if APPLICATION_NUMBER:
        app_number_section = f"""
        <div style="margin-bottom: 20px;">
            <p style="margin: 0; font-size: 14px; color: #333;">
                <strong>Application Reference:</strong> {APPLICATION_NUMBER}
            </p>
        </div>
        """

    if MARKET == "us":
        body_paragraphs = f"""<p>My name is <b>Rachit Jain</b>, and I am a final-year B.Tech student in Computer Software Engineering at Delhi Technological University (DTU), graduating in 2026. I am writing to express my interest in Software Engineer / AI Engineer opportunities at <b>{company}</b>. <b>I am a U.S. citizen, authorized to work for any U.S. employer, with no work sponsorship or relocation assistance required.</b></p>
<p>I have experience across Software Development and AI through internships at MPS Limited, Path Infotech, and Gabbit Trans Systems. My work spans React, Java, Python, Machine Learning, Deep Learning, NLP, Computer Vision, Generative AI, and Agentic AI systems. I have built production-grade web applications, AI-powered automation platforms, LLM-driven workflows, and intelligent agent-based solutions, along with authoring two published research papers in the AI/ML domain.</p>
<p>My recent experience includes developing a React-based digital content management platform for UK Legal Deposit Libraries, building LangGraph-powered AI automation systems, fine-tuning LLaMA-based conversational AI solutions, and developing machine learning applications for real-world use cases.</p>
<p>I would greatly appreciate the opportunity to contribute to <b>{company}</b> and would be grateful if you could consider my profile for any relevant Software Engineer, Machine Learning Engineer, or AI Engineer openings.</p>
<p>I am attaching my resume for your reference.</p>
<p>Thank you for your time and consideration.</p>

<p>Yours sincerely,<br>
<b>Rachit Jain</b><br>
&#128231; <a href="mailto:rachitjainemail@gmail.com">rachitjainemail@gmail.com</a><br>
&#128222; +91-9650090580<br>
<a href="https://github.com/Rachit180">GitHub</a> |
<a href="https://www.linkedin.com/in/rachit-jain-875aa2247/">LinkedIn</a></p>"""
    else:
        body_paragraphs = f"""<p>My name is Rachit Jain, and I am a final-year B.Tech student in Computer Software Engineering at Delhi Technological University (DTU), graduating in 2026. I am writing to express my interest in Software Engineer / AI Engineer opportunities at {company}.</p>
<p>I have experience across Software Development and AI through internships at MPS Limited, Path Infotech, and Gabbit Trans Systems. My work spans React, Java, Python, Machine Learning, Deep Learning, NLP, Computer Vision, Generative AI, and Agentic AI systems. I have built production-grade web applications, AI-powered automation platforms, LLM-driven workflows, and intelligent agent-based solutions, along with authoring two published research papers in the AI/ML domain.</p>
<p>My recent experience includes developing a React-based digital content management platform for UK Legal Deposit Libraries, building LangGraph-powered AI automation systems, fine-tuning LLaMA-based conversational AI solutions, and developing machine learning applications for real-world use cases.</p>
<p>I would greatly appreciate the opportunity to contribute to {company} and would be grateful if you could consider my profile for any relevant Software Engineer, Machine Learning Engineer, or AI Engineer openings.</p>
<p>I am attaching my resume for your reference.</p>
<p>Thank you for your time and consideration.</p>

<p>Yours sincerely,<br>
<b>Rachit Jain</b><br>
&#128231; <a href="mailto:rachitjainemail@gmail.com">rachitjainemail@gmail.com</a><br>
&#128222; +91-9650090580<br>
<a href="https://github.com/Rachit180">GitHub</a> |
<a href="https://www.linkedin.com/in/rachit-jain-875aa2247/">LinkedIn</a></p>"""

    return f"""<html>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #222;">
{app_number_section}
<p>Hello {hiring_manager},</p>

{body_paragraphs}

</body>
</html>"""


def get_subject(company):
    """Build the email subject. Appends application number only if set."""
    base_subject = f"Application for SDE/ AI Engineer Fresher Role - Rachit Jain, DTU at {company}"
    if APPLICATION_NUMBER:
        return f"{base_subject} [{APPLICATION_NUMBER}]"
    return base_subject


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
    msg["Subject"] = get_subject(company)
    body = get_email_body(hiring_manager, company)
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
            requests.get(service_url, timeout=5)
            logger.debug(f"\U0001f504 Keep-alive ping sent ({elapsed}s / {delay_secs}s)")
        except Exception as e:
            logger.debug(f"\u26a0\ufe0f Keep-alive ping failed: {e}")


def send_emails_async():
    """Send emails in background thread"""
    global sending_status

    logger.info(f"\U0001f680 Starting email sending process...")
    logger.info(f"\U0001f30d Target market: {MARKET.upper()} | Resume: {os.path.basename(RESUME_FILE_OVERRIDE)}")
    if APPLICATION_NUMBER:
        logger.info(f"\U0001f4cb Application Number for this run: {APPLICATION_NUMBER}")
    else:
        logger.info("\U0001f4cb No Application Number set - will be omitted from emails")
    sending_status["is_sending"] = True
    sending_status["results"] = []

    # Validate environment variables for HTTPS Mailgun API
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN or not SENDER_ADDRESS:
        error_msg = "Missing required environment variables for HTTPS send: MAILGUN_API_KEY, MAILGUN_DOMAIN, and/or SENDER_ADDRESS"
        logger.error(f"\u274c {error_msg}")
        sending_status["results"].append({
            "status": "error",
            "message": error_msg
        })
        sending_status["is_sending"] = False
        return

    if not os.path.isfile(RESUME_FILE_OVERRIDE):
        error_msg = f"Resume file not found at: {RESUME_FILE_OVERRIDE}"
        logger.error(f"\u274c {error_msg}")
        sending_status["results"].append({
            "status": "error",
            "message": error_msg
        })
        sending_status["is_sending"] = False
        return

    logger.info(f"\U0001f4c4 Reading resume file: {RESUME_FILE_OVERRIDE}")
    with open(RESUME_FILE_OVERRIDE, "rb") as f:
        resume_bytes = f.read()
    resume_filename = os.path.basename(RESUME_FILE_OVERRIDE)
    logger.info(f"\u2705 Resume file loaded: {len(resume_bytes)} bytes")

    # Determine service URL for keep-alive pings
    service_url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000/health")
    if not service_url.endswith("/health"):
        service_url = service_url.rstrip("/") + "/health"

    try:
        logger.info(f"\U0001f310 Using Mailgun HTTPS API (domain={MAILGUN_DOMAIN})")
        logger.info(f"\U0001f4ec Total recipients to send: {len(recipients)}")
        api_base = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        auth = ("api", MAILGUN_API_KEY)

        for idx, (recipient, (hiring_manager, company)) in enumerate(recipients.items(), start=1):
            try:
                logger.info(f"\U0001f4e8 [{idx}/{len(recipients)}] Preparing email for {recipient} \u2014 {hiring_manager} @ {company}")
                subject = get_subject(company)
                html_body = get_email_body(hiring_manager, company)

                data = {
                    "from": SENDER_ADDRESS,
                    "to": recipient,
                    "subject": subject,
                    "html": html_body
                }

                files = [("attachment", (resume_filename, resume_bytes, "application/pdf"))]

                response = requests.post(api_base, auth=auth, data=data, files=files, timeout=60)
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"\u2705 [{idx}/{len(recipients)}] Successfully sent to {recipient} \u2014 {hiring_manager} @ {company}")
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
                    logger.error(f"\u274c [{idx}/{len(recipients)}] Failed to send to {recipient}: {error_msg}")
                    sending_status["results"].append({
                        "status": "error",
                        "recipient": recipient,
                        "error": error_msg
                    })

                if idx < len(recipients):
                    delay_secs = random.randint(600, 700)
                    logger.info(f"\u23f3 Waiting {delay_secs} seconds ({delay_secs//60} minutes) before next email...")
                    logger.info(f"\U0001f504 Keep-alive pings enabled to prevent service spin-down")
                    keep_alive_during_wait(delay_secs, service_url)

            except Exception as send_err:
                error_msg = f"Failed to send to {recipient}: {str(send_err)}"
                logger.error(f"\u274c [{idx}/{len(recipients)}] {error_msg}")
                sending_status["results"].append({
                    "status": "error",
                    "recipient": recipient,
                    "error": str(send_err)
                })

        sending_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"\U0001f389 Email sending completed! Last run: {sending_status['last_run']}")
    finally:
        sending_status["is_sending"] = False
        logger.info("\U0001f3c1 Email sending process finished")


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
        "resume_file_exists": os.path.isfile(RESUME_FILE_OVERRIDE),
        "resume_file": os.path.basename(RESUME_FILE_OVERRIDE),
        "target_market": MARKET.upper(),
        "recipients_count": len(recipients)
    })


@app.route("/send", methods=["POST"])
def send_emails():
    if not check_auth():
        logger.warning("\u26a0\ufe0f Unauthorized access attempt to /send endpoint")
        return jsonify({"error": "Unauthorized"}), 401

    if sending_status["is_sending"]:
        logger.warning("\u26a0\ufe0f Email sending already in progress, request rejected")
        return jsonify({
            "status": "busy",
            "message": "Email sending is already in progress"
        }), 409

    logger.info(f"\U0001f4ec Email sending triggered via API. Recipients: {len(recipients)}")
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
    """Trigger email sending automatically after server is confirmed up"""
    port = int(os.environ.get("PORT", 5000))
    local_url = f"http://127.0.0.1:{port}/health"

    logger.info("\u23f3 Waiting for server to be ready before auto-send...")
    for attempt in range(30):
        try:
            resp = requests.get(local_url, timeout=3)
            if resp.status_code == 200:
                logger.info("\u2705 Server is ready and responding on port %d", port)
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        logger.warning("\u26a0\ufe0f Server readiness check timed out, proceeding with auto-send anyway")

    if not AUTO_SEND:
        logger.info("\u23f8\ufe0f  Auto-send disabled. Set AUTO_SEND=true to enable automatic sending.")
        return

    if sending_status["is_sending"]:
        logger.info("\u23ed\ufe0f  Skipping auto-send - email sending already in progress")
        return

    if sending_status["last_run"]:
        logger.info(f"\u23ed\ufe0f  Skipping auto-send - emails already sent on {sending_status['last_run']}")
        logger.info("\U0001f4a1 To send again, use POST /send endpoint or redeploy the service")
        return

    logger.info("\U0001f916 Auto-send enabled: Starting email sending automatically...")
    logger.info(f"\U0001f4ec Will send to {len(recipients)} recipient(s)")
    thread = threading.Thread(target=send_emails_async)
    thread.daemon = True
    thread.start()


# Start auto-send in background when app initializes
if AUTO_SEND:
    startup_thread = threading.Thread(target=trigger_auto_send)
    startup_thread.daemon = True
    startup_thread.start()
    logger.info("\u2705 Auto-send thread scheduled - will start after server is ready")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
