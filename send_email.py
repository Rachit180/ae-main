#!/usr/bin/env python3
# Har Har Mahadev

import smtplib
import time
import random
import os
import smtplib as _smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Try to load .env file if it exists (for local development)
# On Render, environment variables are set directly, so this is optional
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

# === CONFIGURE FROM ENVIRONMENT ===
# Set these in environment variables; never hardcode
MAILGUN_SMTP_LOGIN = os.environ.get("MAILGUN_SMTP_LOGIN")
MAILGUN_SMTP_PASSWORD = os.environ.get("MAILGUN_SMTP_PASSWORD")
MAILGUN_SMTP_HOST = os.environ.get("MAILGUN_SMTP_HOST", "smtp.mailgun.org")
MAILGUN_SMTP_PORT = int(os.environ.get("MAILGUN_SMTP_PORT", "587"))
SENDER_ADDRESS = os.environ.get("SENDER_ADDRESS", MAILGUN_SMTP_LOGIN)

# Delay configuration (to avoid long idle timeouts)
DELAY_MIN_SECONDS = int(os.environ.get("DELAY_MIN_SECONDS", "600"))
DELAY_MAX_SECONDS = int(os.environ.get("DELAY_MAX_SECONDS", "700"))

# Resume file path (use environment variable or default)
RESUME_FILE = os.environ.get("RESUME_FILE", "RACHITJAIN_RESUME.pdf")

# recipients mapping
recipients = {


"sai.gandlapalli@iongroup.com": ("Sai Gandlapalli", "ION"),
"rashi.pandita@iongroup.com": ("Rashi Pandita", "ION"),
"archana.singh@iongroup.com": ("Archana Singh", "ION"),

 }
#gfh
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

# === Helper to build message ===
def build_message(sender, recipient, hiring_manager, company, resume_bytes, resume_filename):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = f"Application for SDE Fresher Role - Rachit Jain, DTU at {company}"
    body = BODY_TEMPLATE.format(hiring_manager=hiring_manager, company=company)
    msg.attach(MIMEText(body, "html"))

    # attach resume (use bytes already read)
    resume = MIMEApplication(resume_bytes, _subtype="pdf")
    # Put filename in quotes to be safe with spaces
    resume.add_header("Content-Disposition", f'attachment; filename="{resume_filename}"')
    msg.attach(resume)
    return msg

# === SMTP helpers ===
def connect_smtp():
    print(f"📧 Connecting to Mailgun SMTP ({MAILGUN_SMTP_HOST}:{MAILGUN_SMTP_PORT})...")
    server = smtplib.SMTP(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT, timeout=30)
    server.ehlo()
    if MAILGUN_SMTP_PORT == 587:
        server.starttls()
        server.ehlo()
    server.login(MAILGUN_SMTP_LOGIN, MAILGUN_SMTP_PASSWORD)
    print("✅ Successfully connected to Mailgun SMTP")
    return server

def ensure_connection(server):
    try:
        server.noop()
        return server
    except Exception:
        try:
            server.quit()
        except Exception:
            pass
        return connect_smtp()

# === Main send loop (robust with keepalive/reconnect) ===
def main():
    # Validate environment variables
    if not MAILGUN_SMTP_LOGIN or not MAILGUN_SMTP_PASSWORD:
        print("❌ Missing required environment variables: MAILGUN_SMTP_LOGIN and/or MAILGUN_SMTP_PASSWORD")
        return
    
    if not os.path.isfile(RESUME_FILE):
        print(f"❌ Resume file not found at: {RESUME_FILE}")
        return

    with open(RESUME_FILE, "rb") as f:
        resume_bytes = f.read()
    resume_filename = os.path.basename(RESUME_FILE)

    try:
        server = connect_smtp()
    except Exception as e:
        print("❌ Failed to connect/login to Mailgun SMTP:", e)
        return

    try:
        for idx, (recipient, (hiring_manager, company)) in enumerate(recipients.items(), start=1):
            try:
                server = ensure_connection(server)
                msg = build_message(SENDER_ADDRESS, recipient, hiring_manager, company, resume_bytes, resume_filename)
                try:
                    server.sendmail(SENDER_ADDRESS, recipient, msg.as_string())
                except _smtplib.SMTPServerDisconnected:
                    # Reconnect once and retry this recipient
                    server = connect_smtp()
                    server.sendmail(SENDER_ADDRESS, recipient, msg.as_string())
                print(f"✅ ({idx}/{len(recipients)}) Sent to {recipient} — {hiring_manager} @ {company}")
            except Exception as send_err:
                print(f"❌ Failed to send to {recipient}: {send_err}")

            # Random delay between emails to avoid bursts and idle timeouts
            if idx < len(recipients):  # Don't sleep after the last email
                delay_secs = random.randint(max(0, DELAY_MIN_SECONDS), max(DELAY_MIN_SECONDS, DELAY_MAX_SECONDS))
                print(f"⏳ Sleeping for {delay_secs} seconds before next email...\n")
                time.sleep(delay_secs)

    finally:
        try:
            server.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
