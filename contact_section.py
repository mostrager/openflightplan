import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

# ─────────────── Config from .env ───────────────
DB_PATH = "inquiries.db"
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", EMAIL_SENDER)
SMTP_SERVER = os.getenv("SMTP_SERVER", "127.0.0.1")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))
USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# ─────────────── Init DB ───────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ─────────────── Save Inquiry ───────────────
def save_to_db(name: str, email: str, message: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO inquiries (name, email, message) VALUES (?, ?, ?)", (name, email, message))
    conn.commit()
    conn.close()

# ─────────────── Send Email ───────────────
def send_email(name: str, email: str, message: str):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"New Inquiry from {name}"
    body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        if USE_TLS:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)

        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# ─────────────── Form Renderer ───────────────
def render_contact_form():
    st.header("📬 Contact Us")
    st.markdown("Have questions or feedback? Drop us a message!")

    with st.form("contact_form"):
        name = st.text_input("Your Name", max_chars=100)
        email = st.text_input("Your Email", max_chars=100)
        message = st.text_area("Your Message", height=200)
        submitted = st.form_submit_button("Send Message")

        if submitted:
            if not name or not email or not message:
                st.warning("Please fill in all fields.")
            else:
                save_to_db(name, email, message)
                if send_email(name, email, message):
                    st.success("Message sent successfully!")

# Initialize the DB
init_db()
