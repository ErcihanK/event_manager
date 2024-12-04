# smtp_client.py
from builtins import Exception, int, str
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from settings.config import settings
import logging

class SMTPClient:
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool = True):
        self.smtp_host = host
        self.smtp_port = port
        self.smtp_user = username
        self.smtp_pass = password
        self.use_tls = use_tls

    def send_email(self, subject: str, content: str = None, html_content: str = None, recipient: str = None):
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.smtp_user
            message['To'] = recipient
            content_to_send = html_content or content
            message.attach(MIMEText(content_to_send, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(message)  # Use send_message instead of sendmail
            logging.info(f"Email sent to {recipient}")
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise

    def get_server(self):
        return smtplib.SMTP(self.smtp_host, self.smtp_port)

class SMTPConnection:
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool = True):
        self.smtp_host = host
        self.smtp_port = port
        self.smtp_user = username
        self.smtp_pass = password
        self.use_tls = use_tls
        
    def send_email(self, subject: str, content: str, recipient: str):
        """Send an email with error handling."""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                msg = MIMEText(content, 'html')
                msg['Subject'] = subject
                msg['From'] = self.username
                msg['To'] = recipient
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise  # Re-raise the exception for proper error handling
