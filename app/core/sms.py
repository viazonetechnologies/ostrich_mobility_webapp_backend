import os
import requests
from typing import Optional

class SMSService:
    """SMS service with multiple provider support"""
    
    def __init__(self):
        self.provider = os.getenv('SMS_PROVIDER', 'console')  # console, twilio, msg91, fast2sms
        self.is_production = os.getenv('ENVIRONMENT', 'development') == 'production'
    
    def send_otp(self, phone: str, otp: str) -> bool:
        """Send OTP via configured SMS provider"""
        
        if not self.is_production or self.provider == 'console':
            # Development mode: Print to console
            print(f"\n{'='*50}")
            print(f"OTP for {phone}: {otp}")
            print(f"{'='*50}\n")
            return True
        
        # Production mode: Use configured provider
        try:
            if self.provider == 'twilio':
                return self._send_via_twilio(phone, otp)
            elif self.provider == 'msg91':
                return self._send_via_msg91(phone, otp)
            elif self.provider == 'fast2sms':
                return self._send_via_fast2sms(phone, otp)
            else:
                print(f"Unknown SMS provider: {self.provider}")
                return False
        except Exception as e:
            print(f"SMS sending failed: {e}")
            return False
    
    def _send_via_twilio(self, phone: str, otp: str) -> bool:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            if not all([account_sid, auth_token, from_number]):
                raise ValueError("Twilio credentials not configured")
            
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"Your Ostrich Mobility OTP is: {otp}. Valid for 10 minutes.",
                from_=from_number,
                to=phone
            )
            
            print(f"Twilio SMS sent: {message.sid}")
            return True
        except ImportError:
            print("Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            print(f"Twilio error: {e}")
            return False
    
    def _send_via_msg91(self, phone: str, otp: str) -> bool:
        """Send SMS via MSG91 (India)"""
        try:
            auth_key = os.getenv('MSG91_AUTH_KEY')
            template_id = os.getenv('MSG91_TEMPLATE_ID')
            
            if not auth_key:
                raise ValueError("MSG91 auth key not configured")
            
            url = "https://api.msg91.com/api/v5/otp"
            payload = {
                "template_id": template_id,
                "mobile": phone,
                "authkey": auth_key,
                "otp": otp
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print(f"MSG91 SMS sent to {phone}")
                return True
            else:
                print(f"MSG91 error: {response.text}")
                return False
        except Exception as e:
            print(f"MSG91 error: {e}")
            return False
    
    def _send_via_fast2sms(self, phone: str, otp: str) -> bool:
        """Send SMS via Fast2SMS (India)"""
        try:
            api_key = os.getenv('FAST2SMS_API_KEY')
            
            if not api_key:
                raise ValueError("Fast2SMS API key not configured")
            
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "route": "otp",
                "sender_id": "OSTRICH",
                "message": f"Your OTP is {otp}",
                "variables_values": otp,
                "flash": 0,
                "numbers": phone
            }
            headers = {
                "authorization": api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"Fast2SMS sent to {phone}")
                return True
            else:
                print(f"Fast2SMS error: {response.text}")
                return False
        except Exception as e:
            print(f"Fast2SMS error: {e}")
            return False

# Singleton instance
sms_service = SMSService()
