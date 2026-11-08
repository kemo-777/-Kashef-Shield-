import base64
import hashlib
import hmac
import html
import os
import re
import time
from typing import Dict, Any, Tuple

# مفتاح التوقيع المشفر الداخلي لحماية السجلات من التعديل (في بيئة الإنتاج يُخزن في HSM أو Vault)
HMAC_SECRET = os.getenv("FRAUD_HMAC_SECRET", "super_secret_bank_grade_key_2026_xyz").encode()

class CyberSecurityShield:
    def __init__(self, max_requests_per_minute: int = 60):
        self.rate_limit_window = 60.0
        self.max_requests = max_requests_per_minute
        self.client_requests: Dict[str, list] = {}

    def enforce_rate_limiting(self, client_id: str) -> bool:
        """منع هجمات حجب الخدمة (DDoS) ومنع كشف عتبات الذكاء الاصطناعي (Brute-force)"""
        now = time.time()
        if client_id not in self.client_requests:
            self.client_requests[client_id] = []
        
        # تصفية الطلبات القديمة التي تجاوزت الدقيقة
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id] 
            if now - req_time < self.rate_limit_window
        ]

        if len(self.client_requests[client_id]) >= self.max_requests:
            return False  # تجاوز الحد المسموح
        
        self.client_requests[client_id].append(now)
        return True

    @staticmethod
    def sanitize_input(text: str) -> str:
        """تنظيف وتطهير النصوص لمنع هجمات XSS وScript Injections"""
        if not isinstance(text, str):
            return str(text)
        # إزالة العلامات المشبوهة والتحويل إلى صيغة نصية آمنة
        clean = html.escape(text.strip())
        clean = re.sub(r'[<>{}\;]', '', clean)
        return clean

    @staticmethod
    def mask_card_token(token: str) -> str:
        """حجب بيانات البطاقة وحمايتها وفقاً لمعيار PCI-DSS"""
        if len(token) <= 4:
            return "****"
        return f"****-****-****-{token[-4:]}"

    @staticmethod
    def generate_audit_signature(payload_data: Dict[str, Any]) -> str:
        """توقيع مشفر يثبت عدم تعديل السجل المالي لاحقاً (Integrity Check)"""
        raw_msg = f"{payload_data.get('transaction_id')}_{payload_data.get('amount')}_{payload_data.get('decision')}_{payload_data.get('timestamp')}"
        signature = hmac.new(HMAC_SECRET, raw_msg.encode(), hashlib.sha256).hexdigest()
        return signature[:20]