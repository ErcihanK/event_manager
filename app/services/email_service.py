# email_service.py
from builtins import ValueError, dict, str
from settings.config import settings
from app.utils.smtp_connection import SMTPClient
from app.utils.template_manager import TemplateManager
from app.models.user_model import User

class EmailService:
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
        self.smtp_client = SMTPClient(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass"
        )

    async def send_user_email(self, user_data: dict, email_type: str):
        subject_map = {
            'email_verification': "Verify Your Account",
            'verification_email': "Verify Your Account",
            'password_reset': "Password Reset Instructions",
            'account_locked': "Account Locked Notification"
        }

        if email_type not in subject_map:
            raise ValueError(f"Invalid email type: {email_type}")

        html_content = self.template_manager.render_email_template(email_type, user_data)
        self.smtp_client.send_email(subject_map[email_type], html_content, user_data['email'])

    async def send_verification_email(self, user: User):
        verification_url = f"{settings.server_base_url}verify-email/{user.id}/{user.verification_token}"
        await self.send_user_email({
            "name": user.first_name,
            "verification_url": verification_url,
            "email": user.email
        }, 'email_verification')