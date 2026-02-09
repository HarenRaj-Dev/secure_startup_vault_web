from flask_mail import Message
from vault import mail
from flask import url_for, current_app
from threading import Thread
import smtplib

def send_async_email(app, msg):
    with app.app_context():
        smtp_server = app.config.get('MAIL_SERVER')
        smtp_port = app.config.get('MAIL_PORT')
        smtp_user = app.config.get('MAIL_USERNAME')
        smtp_password = app.config.get('MAIL_PASSWORD')
        
        try:
            print(f"\n[DEBUG] Connecting to SMTP: {smtp_server}:{smtp_port} as {smtp_user}...")
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.set_debuglevel(0) # Set to 1 for verbose output if needed
                server.starttls()
                server.login(smtp_user, smtp_password)
                
                # Construct email from Flask-Mail Message object
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                email_msg = MIMEMultipart()
                email_msg['From'] = msg.sender
                email_msg['To'] = ", ".join(msg.recipients)
                email_msg['Subject'] = msg.subject
                email_msg.attach(MIMEText(msg.body, 'plain'))
                
                server.send_message(email_msg)
                print("[DEBUG] Email sent successfully via smtplib!")

        except (smtplib.SMTPException, ConnectionRefusedError, OSError) as e:
            print(f"\n[EMAIL ERROR] Could not send email: {e}")
            print(f"[TIP] Check your .env file. MAIL_USERNAME and MAIL_PASSWORD must be correct.")
            print(f"[TIP] Ensure 'Less secure apps' or 'App Passwords' are enabled for Gmail.\n")
        except Exception as e:
             print(f"\n[EMAIL ERROR] Unexpected error sending email: {e}\n")

def send_otp_email(user):
    otp = user.otp_code
    msg = Message('Login OTP - Secure Startup Vault',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    msg.body = f'''To log in to your Secure Startup Vault account, use the following One-Time Password (OTP):

{otp}

This OTP is valid for 10 minutes.
If you did not request this, please ignore this email.
'''
    # Send asynchronously
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
