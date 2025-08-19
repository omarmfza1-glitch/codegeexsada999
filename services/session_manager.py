# === مدير الجلسات ===
# هذا المدير يدير جميع جلسات العمل النشطة ويوفر واجهة للوصول إليها

import uuid
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """
    مدير الجلسات - مسؤول عن إنشاء وإدارة جلسات العمل النشطة
    """

    def __init__(self):
        """تهيئة مدير الجلسات"""
        self.active_sessions: Dict[str, Dict] = {}

    def create_session(self, session_id: str, from_number: str, call_sid: str) -> Dict:
        """
        إنشاء جلسة جديدة

        Args:
            session_id: معرف فريد للجلسة
            from_number: رقم المتصل
            call_sid: معرف المكالمة من Twilio

        Returns:
            معلومات الجلسة المنشأة
        """
        session_info = {
            "session_id": session_id,
            "from_number": from_number,
            "call_sid": call_sid,
            "start_time": time.time(),
            "last_activity": time.time(),
            "language": None,
            "status": "active"
        }

        self.active_sessions[session_id] = session_info
        logger.info(f"تم إنشاء جلسة جديدة: {session_id} للمتصل: {from_number}")

        return session_info

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        الحصول على معلومات الجلسة

        Args:
            session_id: معرف الجلسة

        Returns:
            معلومات الجلسة أو None إذا لم توجد
        """
        return self.active_sessions.get(session_id)

    def get_session_by_call_sid(self, call_sid: str) -> Optional[Dict]:
        """
        الحصول على الجلسة عبر معرف المكالمة

        Args:
            call_sid: معرف المكالمة من Twilio

        Returns:
            معلومات الجلسة أو None إذا لم توجد
        """
        for session in self.active_sessions.values():
            if session["call_sid"] == call_sid:
                return session
        return None

    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        تحديث معلومات الجلسة

        Args:
            session_id: معرف الجلسة
            **kwargs: سمات التحديث

        Returns:
            True إذا نجح التحديث، False إذا فشل
        """
        if session_id not in self.active_sessions:
            return False

        self.active_sessions[session_id].update(kwargs)
        self.active_sessions[session_id]["last_activity"] = time.time()
        return True

    def end_session(self, session_id: str) -> bool:
        """
        إنهاء جلسة نشطة

        Args:
            session_id: معرف الجلسة

        Returns:
            True إذا نجح الإنهاء، False إذا فشل
        """
        if session_id not in self.active_sessions:
            return False

        self.active_sessions[session_id]["status"] = "ended"
        self.active_sessions[session_id]["end_time"] = time.time()
        logger.info(f"تم إنهاء الجلسة: {session_id}")
        return True

    def get_active_sessions_count(self) -> int:
        """
        الحصول على عدد الجلسات النشطة

        Returns:
            عدد الجلسات النشطة
        """
        return len([s for s in self.active_sessions.values() if s["status"] == "active"])

    def cleanup_inactive_sessions(self, timeout_seconds: int = 3600) -> int:
        """
        تنظيف الجلسات غير النشطة التي انتهت مهلتها

        Args:
            timeout_seconds: عدد الثواني التي يجب أن تكون الجلسة غير نشطة فيها

        Returns:
            عدد الجلسات التي تم تنظيفها
        """
        current_time = time.time()
        cleaned_count = 0

        for session_id, session in list(self.active_sessions.items()):
            if (session["status"] == "active" and 
                current_time - session["last_activity"] > timeout_seconds):
                self.end_session(session_id)
                cleaned_count += 1

        return cleaned_count
