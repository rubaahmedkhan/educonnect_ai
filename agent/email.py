import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = ""
EMAIL_PASSWORD = ""

def send_email(to_email, subject, body):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise Exception("Please set EMAIL_ADDRESS and EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}. Error: {e}")
        raise e

def send_email_report(df, feedback_data):
    # Validate inputs
    if not feedback_data:
        raise ValueError("No feedback data provided.")
    
    if len(feedback_data) != len(df):
        raise ValueError(f"Mismatch between number of students ({len(df)}) and feedbacks ({len(feedback_data)}).")

    for feedback in feedback_data:
        name = feedback.get("name")
        to_email = feedback.get("email")
        body = feedback.get("feedback")

        if not to_email:
            print(f"⚠️ Skipping email for {name}: No email address found.")
            continue

        subject = f"Your Feedback Report - {name}"
        try:
            send_email(to_email, subject, body)
        except Exception as e:
            print(f"❌ Error sending email to {name} ({to_email}): {str(e)}")
            raise e

