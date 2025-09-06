# import smtplib
# import jwt
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from datetime import datetime, timedelta
# from typing import Dict, Any
# from utils.config import config
# import logging
# import os

# logger = logging.getLogger(__name__)

# class EmailApprovalService:
#     """Service for sending approval emails and generating secure tokens"""
    
#     def __init__(self):
#         self.smtp_server = getattr(config, 'SMTP_SERVER', 'smtp.gmail.com')
#         self.smtp_port = getattr(config, 'SMTP_PORT', 587)
#         self.smtp_user = getattr(config, 'SMTP_USER', None)
#         self.smtp_password = getattr(config, 'SMTP_PASSWORD', None)
#         self.from_email = getattr(config, 'FROM_EMAIL', self.smtp_user)
        
#         # Use Streamlit app URL for approval links
#         self.approval_app_url = os.getenv('APPROVAL_APP_URL', 'https://podcast-approval.streamlit.app')
#         self.backend_api_url = os.getenv('BACKEND_API_URL', 'http://localhost:5050')
#         self.secret_key = getattr(config, 'EMAIL_SECRET_KEY', 'change-this-secret-key')
    
#     def generate_approval_token(self, job_id: str, stage: str, action: str) -> str:
#         """Generate a secure token for approval actions"""
#         payload = {
#             'job_id': job_id,
#             'stage': stage,
#             'action': action,
#             'backend_url': self.backend_api_url,  # Include backend URL in token
#             'exp': datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
#             'iat': datetime.utcnow()
#         }
#         return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
#     def send_outline_approval_email(self, job_id: str, user_email: str, outline_data: Dict[str, Any]) -> bool:
#         """Send outline approval email"""
#         try:
#             approve_token = self.generate_approval_token(job_id, 'outline', 'approve')
#             reject_token = self.generate_approval_token(job_id, 'outline', 'reject')
            
#             subject = f"Podcast Outline Approval Required - Job {job_id}"
#             html_content = self._create_outline_email_html(
#                 job_id, outline_data, approve_token, reject_token
#             )
            
#             return self._send_email(user_email, subject, html_content)
#         except Exception as e:
#             logger.error(f"Failed to send outline approval email for job {job_id}: {e}")
#             return False
    
#     def send_script_approval_email(self, job_id: str, user_email: str, script_data: Dict[str, Any]) -> bool:
#         """Send script approval email"""
#         try:
#             approve_token = self.generate_approval_token(job_id, 'script', 'approve')
#             reject_token = self.generate_approval_token(job_id, 'script', 'reject')
            
#             subject = f"Podcast Script Approval Required - Job {job_id}"
#             html_content = self._create_script_email_html(
#                 job_id, script_data, approve_token, reject_token
#             )
            
#             return self._send_email(user_email, subject, html_content)
#         except Exception as e:
#             logger.error(f"Failed to send script approval email for job {job_id}: {e}")
#             return False
    
#     def send_audio_approval_email(self, job_id: str, user_email: str, audio_data: Dict[str, Any]) -> bool:
#         """Send audio approval email"""
#         try:
#             approve_token = self.generate_approval_token(job_id, 'audio', 'approve')
#             reject_token = self.generate_approval_token(job_id, 'audio', 'reject')
            
#             subject = f"Podcast Audio Approval Required - Job {job_id}"
#             html_content = self._create_audio_email_html(
#                 job_id, audio_data, approve_token, reject_token
#             )
            
#             return self._send_email(user_email, subject, html_content)
#         except Exception as e:
#             logger.error(f"Failed to send audio approval email for job {job_id}: {e}")
#             return False
    
#     def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
#         """Send email via SMTP"""
#         try:
#             if not self.smtp_user or not self.smtp_password:
#                 logger.error("SMTP credentials not configured")
#                 return False
            
#             msg = MIMEMultipart('alternative')
#             msg['Subject'] = subject
#             msg['From'] = self.from_email
#             msg['To'] = to_email
            
#             html_part = MIMEText(html_content, 'html')
#             msg.attach(html_part)
            
#             with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
#                 server.starttls()
#                 server.login(self.smtp_user, self.smtp_password)
#                 server.send_message(msg)
            
#             logger.info(f"Approval email sent successfully to {to_email}")
#             return True
#         except Exception as e:
#             logger.error(f"Failed to send email to {to_email}: {e}")
#             return False
    
#     def _create_outline_email_html(self, job_id: str, outline_data: Dict[str, Any], 
#                                    approve_token: str, reject_token: str) -> str:
#         """Create HTML content for outline approval email"""
#         outline = outline_data.get('outline', {})
        
#         # Use Streamlit app URL
#         approve_url = f"{self.approval_app_url}?token={approve_token}"
#         reject_url = f"{self.approval_app_url}?token={reject_token}"
        
#         sections_html = ""
#         for i, section in enumerate(outline.get('sections', []), 1):
#             sections_html += f"""
#             <div style="margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
#                 <h4 style="margin: 0 0 5px 0; color: #495057;">{i}. {section.get('title', '')}</h4>
#                 <p style="margin: 0; color: #6c757d;">{section.get('content', '')}</p>
#             </div>
#             """
        
#         return f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="utf-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <title>Podcast Outline Approval</title>
#         </head>
#         <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
#             <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 5px; text-align: center;">
#                 <h1 style="margin: 0;">🎙️ Podcast Outline Approval</h1>
#                 <p style="margin: 5px 0 0 0;">Job ID: {job_id}</p>
#             </div>
            
#             <div style="padding: 20px; background-color: white; border: 1px solid #dee2e6; border-radius: 5px; margin-top: 20px;">
#                 <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📋 Outline Details</h2>
                
#                 <div style="margin-bottom: 20px;">
#                     <h3 style="color: #007bff; margin-bottom: 10px;">Title</h3>
#                     <p style="font-size: 18px; font-weight: bold; margin: 0;">{outline.get('title', '')}</p>
#                 </div>
                
#                 <div style="margin-bottom: 20px;">
#                     <h3 style="color: #007bff; margin-bottom: 10px;">Introduction</h3>
#                     <p style="margin: 0; padding: 10px; background-color: #e9ecef; border-radius: 5px;">{outline.get('introduction', '')}</p>
#                 </div>
                
#                 <div style="margin-bottom: 20px;">
#                     <h3 style="color: #007bff; margin-bottom: 10px;">Sections</h3>
#                     {sections_html}
#                 </div>
                
#                 <div style="margin-bottom: 20px;">
#                     <h3 style="color: #007bff; margin-bottom: 10px;">Conclusion</h3>
#                     <p style="margin: 0; padding: 10px; background-color: #e9ecef; border-radius: 5px;">{outline.get('conclusion', '')}</p>
#                 </div>
                
#                 <div style="margin-bottom: 20px;">
#                     <h3 style="color: #007bff; margin-bottom: 10px;">Estimated Duration</h3>
#                     <p style="margin: 0; font-weight: bold;">{outline.get('estimated_duration', 'N/A')} minutes</p>
#                 </div>
#             </div>
            
#             <div style="text-align: center; margin-top: 30px;">
#                 <a href="{approve_url}" style="display: inline-block; background-color: #28a745; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">✅ APPROVE</a>
#                 <a href="{reject_url}" style="display: inline-block; background-color: #dc3545; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">❌ REJECT</a>
#             </div>
            
#             <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
#                 <p style="margin: 0; font-size: 14px; color: #856404;">
#                     <strong>Note:</strong> This approval request will expire in 7 days. Please review and take action promptly.
#                 </p>
#             </div>
#         </body>
#         </html>
#         """
    
#     def _create_script_email_html(self, job_id: str, script_data: Dict[str, Any], 
#                                   approve_token: str, reject_token: str) -> str:
#         """Create HTML content for script approval email"""
#         script = script_data.get('script', '')
#         # Truncate script if too long for email
#         script_preview = script[:2000] + "..." if len(script) > 2000 else script
        
#         # Use Streamlit app URL
#         approve_url = f"{self.approval_app_url}?token={approve_token}"
#         reject_url = f"{self.approval_app_url}?token={reject_token}"
        
#         return f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="utf-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <title>Podcast Script Approval</title>
#         </head>
#         <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
#             <div style="background-color: #17a2b8; color: white; padding: 20px; border-radius: 5px; text-align: center;">
#                 <h1 style="margin: 0;">📝 Podcast Script Approval</h1>
#                 <p style="margin: 5px 0 0 0;">Job ID: {job_id}</p>
#             </div>
            
#             <div style="padding: 20px; background-color: white; border: 1px solid #dee2e6; border-radius: 5px; margin-top: 20px;">
#                 <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📜 Script Content</h2>
                
#                 <div style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; max-height: 400px; overflow-y: auto;">
#                     <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; margin: 0; font-size: 14px;">{script_preview}</pre>
#                 </div>
                
#                 <div style="margin-bottom: 20px;">
#                     <p style="margin: 0; font-size: 14px; color: #6c757d;">
#                         <strong>Script Length:</strong> {len(script)} characters
#                     </p>
#                 </div>
#             </div>
            
#             <div style="text-align: center; margin-top: 30px;">
#                 <a href="{approve_url}" style="display: inline-block; background-color: #28a745; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">✅ APPROVE</a>
#                 <a href="{reject_url}" style="display: inline-block; background-color: #dc3545; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">❌ REJECT</a>
#             </div>
            
#             <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
#                 <p style="margin: 0; font-size: 14px; color: #856404;">
#                     <strong>Note:</strong> This approval request will expire in 7 days. Please review and take action promptly.
#                 </p>
#             </div>
#         </body>
#         </html>
#         """
    
#     def _create_audio_email_html(self, job_id: str, audio_data: Dict[str, Any], 
#                                  approve_token: str, reject_token: str) -> str:
#         """Create HTML content for audio approval email"""
#         audio_url = audio_data.get('audio_url', '')
        
#         # Use Streamlit app URL
#         approve_url = f"{self.approval_app_url}?token={approve_token}"
#         reject_url = f"{self.approval_app_url}?token={reject_token}"
        
#         return f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="utf-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <title>Podcast Audio Approval</title>
#         </head>
#         <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
#             <div style="background-color: #6f42c1; color: white; padding: 20px; border-radius: 5px; text-align: center;">
#                 <h1 style="margin: 0;">🎵 Podcast Audio Approval</h1>
#                 <p style="margin: 5px 0 0 0;">Job ID: {job_id}</p>
#             </div>
            
#             <div style="padding: 20px; background-color: white; border: 1px solid #dee2e6; border-radius: 5px; margin-top: 20px;">
#                 <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">🎧 Audio Preview</h2>
                
#                 <div style="margin-bottom: 20px; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
#                     <audio controls style="width: 100%; max-width: 400px;">
#                         <source src="{audio_url}" type="audio/mpeg">
#                         Your browser does not support the audio element.
#                     </audio>
#                 </div>
                
#                 <div style="margin-bottom: 20px;">
#                     <p style="margin: 0; font-size: 14px; color: #6c757d;">
#                         <strong>Audio URL:</strong> <a href="{audio_url}" target="_blank" style="color: #007bff;">Listen in new tab</a>
#                     </p>
#                 </div>
#             </div>
            
#             <div style="text-align: center; margin-top: 30px;">
#                 <a href="{approve_url}" style="display: inline-block; background-color: #28a745; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">✅ APPROVE</a>
#                 <a href="{reject_url}" style="display: inline-block; background-color: #dc3545; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">❌ REJECT</a>
#             </div>
            
#             <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
#                 <p style="margin: 0; font-size: 14px; color: #856404;">
#                     <strong>Note:</strong> This approval request will expire in 7 days. Please review and take action promptly.
#                 </p>
#             </div>
#         </body>
#         </html>
#         """
import smtplib
import jwt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any
from utils.config import config
import logging
import os

logger = logging.getLogger(__name__)

class EmailApprovalService:
    """Service for sending approval emails and generating secure tokens"""
    
    def __init__(self):
        self.smtp_server = getattr(config, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(config, 'SMTP_PORT', 587)
        self.smtp_user = getattr(config, 'SMTP_USER', None)
        self.smtp_password = getattr(config, 'SMTP_PASSWORD', None)
        self.from_email = getattr(config, 'FROM_EMAIL', self.smtp_user)
        
        # Use the correct Streamlit app URL
        self.approval_app_url = os.getenv('APPROVAL_APP_URL', 'https://approval-app.streamlit.app')
        self.backend_api_url = os.getenv('BACKEND_API_URL', 'https://c15ccbaa9f46.ngrok-free.app')
        
        # Use consistent secret key
        self.secret_key = (
            getattr(config, 'EMAIL_SECRET_KEY', None) or 
            os.getenv('EMAIL_SECRET_KEY') or 
            'change-this-secret-key'
        )
        
        logger.info(f"Email service initialized:")
        logger.info(f"  - Approval app URL: {self.approval_app_url}")
        logger.info(f"  - Backend API URL: {self.backend_api_url}")
        logger.info(f"  - Secret key length: {len(self.secret_key)}")
    
    def generate_approval_token(self, job_id: str, stage: str, action: str) -> str:
        """Generate a secure token for approval actions"""
        payload = {
            'job_id': job_id,
            'stage': stage,
            'action': action,
            'backend_url': self.backend_api_url,  # Include backend URL in token
            'exp': datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        logger.info(f"Generated token for {job_id}-{stage}-{action}: {token[:50]}...")
        return token
    
    def send_outline_approval_email(self, job_id: str, user_email: str, outline_data: Dict[str, Any]) -> bool:
        """Send outline approval email"""
        try:
            logger.info(f"Sending outline approval email for job {job_id} to {user_email}")
            
            approve_token = self.generate_approval_token(job_id, 'outline', 'approve')
            reject_token = self.generate_approval_token(job_id, 'outline', 'reject')
            
            subject = f"Podcast Outline Approval Required - Job {job_id}"
            html_content = self._create_outline_email_html(
                job_id, outline_data, approve_token, reject_token
            )
            
            success = self._send_email(user_email, subject, html_content)
            if success:
                logger.info(f"Outline approval email sent successfully for job {job_id}")
            else:
                logger.error(f"Failed to send outline approval email for job {job_id}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to send outline approval email for job {job_id}: {e}")
            return False
    
    def send_script_approval_email(self, job_id: str, user_email: str, script_data: Dict[str, Any]) -> bool:
        """Send script approval email"""
        try:
            logger.info(f"Sending script approval email for job {job_id} to {user_email}")
            
            approve_token = self.generate_approval_token(job_id, 'script', 'approve')
            reject_token = self.generate_approval_token(job_id, 'script', 'reject')
            
            subject = f"Podcast Script Approval Required - Job {job_id}"
            html_content = self._create_script_email_html(
                job_id, script_data, approve_token, reject_token
            )
            
            success = self._send_email(user_email, subject, html_content)
            if success:
                logger.info(f"Script approval email sent successfully for job {job_id}")
            else:
                logger.error(f"Failed to send script approval email for job {job_id}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to send script approval email for job {job_id}: {e}")
            return False
    
    def send_audio_approval_email(self, job_id: str, user_email: str, audio_data: Dict[str, Any]) -> bool:
        """Send audio approval email"""
        try:
            logger.info(f"Sending audio approval email for job {job_id} to {user_email}")
            
            approve_token = self.generate_approval_token(job_id, 'audio', 'approve')
            reject_token = self.generate_approval_token(job_id, 'audio', 'reject')
            
            subject = f"Podcast Audio Approval Required - Job {job_id}"
            html_content = self._create_audio_email_html(
                job_id, audio_data, approve_token, reject_token
            )
            
            success = self._send_email(user_email, subject, html_content)
            if success:
                logger.info(f"Audio approval email sent successfully for job {job_id}")
            else:
                logger.error(f"Failed to send audio approval email for job {job_id}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to send audio approval email for job {job_id}: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SMTP"""
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Approval email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _create_outline_email_html(self, job_id: str, outline_data: Dict[str, Any], 
                                   approve_token: str, reject_token: str) -> str:
        """Create HTML content for outline approval email"""
        outline = outline_data.get('outline', {})
        
        # Use the correct Streamlit app URL with proper URL encoding
        approve_url = f"{self.approval_app_url}?token={approve_token}"
        reject_url = f"{self.approval_app_url}?token={reject_token}"
        
        logger.info(f"Generated approval URLs for job {job_id}:")
        logger.info(f"  - Approve: {approve_url[:100]}...")
        logger.info(f"  - Reject: {reject_url[:100]}...")
        
        sections_html = ""
        for i, section in enumerate(outline.get('sections', []), 1):
            sections_html += f"""
            <div style="margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                <h4 style="margin: 0 0 5px 0; color: #495057;">{i}. {section.get('title', '')}</h4>
                <p style="margin: 0; color: #6c757d;">{section.get('content', '')}</p>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Podcast Outline Approval</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 5px; text-align: center;">
                <h1 style="margin: 0;">🎙️ Podcast Outline Approval</h1>
                <p style="margin: 5px 0 0 0;">Job ID: {job_id}</p>
            </div>
            
            <div style="padding: 20px; background-color: white; border: 1px solid #dee2e6; border-radius: 5px; margin-top: 20px;">
                <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📋 Outline Details</h2>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #007bff; margin-bottom: 10px;">Title</h3>
                    <p style="font-size: 18px; font-weight: bold; margin: 0;">{outline.get('title', '')}</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #007bff; margin-bottom: 10px;">Introduction</h3>
                    <p style="margin: 0; padding: 10px; background-color: #e9ecef; border-radius: 5px;">{outline.get('introduction', '')}</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #007bff; margin-bottom: 10px;">Sections</h3>
                    {sections_html}
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #007bff; margin-bottom: 10px;">Conclusion</h3>
                    <p style="margin: 0; padding: 10px; background-color: #e9ecef; border-radius: 5px;">{outline.get('conclusion', '')}</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #007bff; margin-bottom: 10px;">Estimated Duration</h3>
                    <p style="margin: 0; font-weight: bold;">{outline.get('estimated_duration', 'N/A')} minutes</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="{approve_url}" style="display: inline-block; background-color: #28a745; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">✅ APPROVE</a>
                <a href="{reject_url}" style="display: inline-block; background-color: #dc3545; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">❌ REJECT</a>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
                <p style="margin: 0; font-size: 14px; color: #856404;">
                    <strong>Note:</strong> This approval request will expire in 7 days. Please review and take action promptly.
                </p>
            </div>
            
            <!-- Debug Information (hidden by default) -->
            <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; color: #666;">
                <p><strong>Debug Info:</strong></p>
                <p>Approve Token: {approve_token[:50]}...</p>
                <p>Reject Token: {reject_token[:50]}...</p>
                <p>Backend URL: {self.backend_api_url}</p>
            </div>
        </body>
        </html>
        """
    
    def _create_script_email_html(self, job_id: str, script_data: Dict[str, Any], 
                                  approve_token: str, reject_token: str) -> str:
        """Create HTML content for script approval email"""
        script = script_data.get('script', '')
        # Truncate script if too long for email
        script_preview = script[:2000] + "..." if len(script) > 2000 else script
        
        # Use the correct Streamlit app URL
        approve_url = f"{self.approval_app_url}?token={approve_token}"
        reject_url = f"{self.approval_app_url}?token={reject_token}"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Podcast Script Approval</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #17a2b8; color: white; padding: 20px; border-radius: 5px; text-align: center;">
                <h1 style="margin: 0;">📝 Podcast Script Approval</h1>
                <p style="margin: 5px 0 0 0;">Job ID: {job_id}</p>
            </div>
            
            <div style="padding: 20px; background-color: white; border: 1px solid #dee2e6; border-radius: 5px; margin-top: 20px;">
                <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📜 Script Content</h2>
                
                <div style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; max-height: 400px; overflow-y: auto;">
                    <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; margin: 0; font-size: 14px;">{script_preview}</pre>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <p style="margin: 0; font-size: 14px; color: #6c757d;">
                        <strong>Script Length:</strong> {len(script)} characters
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="{approve_url}" style="display: inline-block; background-color: #28a745; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">✅ APPROVE</a>
                <a href="{reject_url}" style="display: inline-block; background-color: #dc3545; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">❌ REJECT</a>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
                <p style="margin: 0; font-size: 14px; color: #856404;">
                    <strong>Note:</strong> This approval request will expire in 7 days. Please review and take action promptly.
                </p>
            </div>
            
            <!-- Debug Information -->
            <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; color: #666;">
                <p><strong>Debug Info:</strong></p>
                <p>Approve Token: {approve_token[:50]}...</p>
                <p>Backend URL: {self.backend_api_url}</p>
            </div>
        </body>
        </html>
        """
    
    def _create_audio_email_html(self, job_id: str, audio_data: Dict[str, Any], 
                                 approve_token: str, reject_token: str) -> str:
        """Create HTML content for audio approval email"""
        audio_url = audio_data.get('audio_url', '')
        
        # Use the correct Streamlit app URL
        approve_url = f"{self.approval_app_url}?token={approve_token}"
        reject_url = f"{self.approval_app_url}?token={reject_token}"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Podcast Audio Approval</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #6f42c1; color: white; padding: 20px; border-radius: 5px; text-align: center;">
                <h1 style="margin: 0;">🎵 Podcast Audio Approval</h1>
                <p style="margin: 5px 0 0 0;">Job ID: {job_id}</p>
            </div>
            
            <div style="padding: 20px; background-color: white; border: 1px solid #dee2e6; border-radius: 5px; margin-top: 20px;">
                <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">🎧 Audio Preview</h2>
                
                <div style="margin-bottom: 20px; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                    <audio controls style="width: 100%; max-width: 400px;">
                        <source src="{audio_url}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <p style="margin: 0; font-size: 14px; color: #6c757d;">
                        <strong>Audio URL:</strong> <a href="{audio_url}" target="_blank" style="color: #007bff;">Listen in new tab</a>
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="{approve_url}" style="display: inline-block; background-color: #28a745; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">✅ APPROVE</a>
                <a href="{reject_url}" style="display: inline-block; background-color: #dc3545; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 0 10px;">❌ REJECT</a>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
                <p style="margin: 0; font-size: 14px; color: #856404;">
                    <strong>Note:</strong> This approval request will expire in 7 days. Please review and take action promptly.
                </p>
            </div>
            
            <!-- Debug Information -->
            <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; color: #666;">
                <p><strong>Debug Info:</strong></p>
                <p>Approve Token: {approve_token[:50]}...</p>
                <p>Audio URL: {audio_url}</p>
                <p>Backend URL: {self.backend_api_url}</p>
            </div>
        </body>
        </html>
        """