import smtplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
PORT = int(os.environ.get('MAIL_PORT', 587))
USERNAME = os.environ.get('MAIL_USERNAME')
PASSWORD = os.environ.get('MAIL_PASSWORD')

print(f"--- SMTP DEBUG CONFIG ---")
print(f"Server:   {SERVER}")
print(f"Port:     {PORT}")
print(f"Username: {USERNAME}")
print(f"Password: {'*' * 8 if PASSWORD else 'NOT SET'}")
print(f"-------------------------")

try:
    print(f"Attempting to connect to {SERVER}:{PORT}...")
    server = smtplib.SMTP(SERVER, PORT)
    server.set_debuglevel(1)  # Show low-level communication
    
    print("Starting TLS...")
    server.starttls()
    
    print("Logging in...")
    server.login(USERNAME, PASSWORD)
    
    print("\nSUCCESS! Connection and Login successful.")
    server.quit()
except Exception as e:
    print(f"\nFAILURE: {e}")
