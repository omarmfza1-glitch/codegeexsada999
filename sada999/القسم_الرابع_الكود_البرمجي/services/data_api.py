# === واجهة برمجة تطبيقات البيانات ===
# هذه الخدمة تتعامل مع استعلامات قاعدة بيانات العميل وتوفر البيانات المطلوبة

import os
import logging
import json
from typing import Dict, Optional, List, Any
import requests
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class DataAPI:
    """
    واجهة برمجة تطبيقات البيانات - تتعامل مع استعلامات قاعدة بيانات العميل
    توفر واجهة موحدة للوصول إلى أنواع مختلفة من البيانات
    """

    def __init__(self):
        """تهيئة واجهة برمجة تطبيقات البيانات"""
        self.api_base_url = os.getenv("CUSTOMER_API_BASE_URL", "https://customer-api.example.com")
        self.api_key = os.getenv("CUSTOMER_API_KEY")
        self.timeout = int(os.getenv("API_TIMEOUT", "30"))

        # تهيئة نظام التخزين المؤقت
        self.cache = {}
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # ساعة واحدة

        # تحميل تعريفات الاستعلامات
        self._load_query_definitions()

    def _load_query_definitions(self):
        """تحميل تعريفات الاستعلامات المختلفة"""
        try:
            # في التطبيق الفعلي، سيتم تحميل هذه التعريفات من ملف أو قاعدة بيانات
            # هذا مثال افتراضي
            self.query_definitions = {
                "appointment_booking": {
                    "endpoint": "/appointments",
                    "method": "POST",
                    "required_params": ["date", "time", "service_type"],
                    "optional_params": ["doctor_name", "location"],
                    "response_mapping": {
                        "appointment_id": "id",
                        "appointment_date": "date",
                        "appointment_time": "time",
                        "doctor_name": "doctor",
                        "status": "status"
                    }
                },
                "shipment_inquiry": {
                    "endpoint": "/shipments/{tracking_id}",
                    "method": "GET",
                    "required_params": ["tracking_id"],
                    "optional_params": [],
                    "response_mapping": {
                        "tracking_number": "tracking_id",
                        "status": "status",
                        "location": "current_location",
                        "estimated_delivery": "estimated_delivery_date",
                        "carrier": "carrier"
                    }
                },
                "account_balance": {
                    "endpoint": "/accounts/{account_id}/balance",
                    "method": "GET",
                    "required_params": ["account_id"],
                    "optional_params": ["currency"],
                    "response_mapping": {
                        "account_id": "account_id",
                        "balance": "balance",
                        "currency": "currency",
                        "last_updated": "last_updated"
                    }
                },
                "general_inquiry": {
                    "endpoint": "/search",
                    "method": "GET",
                    "required_params": ["query"],
                    "optional_params": ["category", "limit"],
                    "response_mapping": {
                        "results": "results",
                        "total_count": "total"
                    }
                }
            }

            logger.info("تم تحميل تعريفات الاستعلامات بنجاح")
        except Exception as e:
            logger.error(f"فشل في تحميل تعريفات الاستعلامات: {str(e)}")
            self.query_definitions = {}

    def query_data(self, intent: str, entities: Dict[str, Any], language: str = "ar") -> Dict[str, Any]:
        """
        استعلام البيانات بناءً على النية والكيانات

        Args:
            intent: النية المحددة
            entities: الكيانات المستخرجة
            language: لغة الاستجابة

        Returns:
            قاموس يحتوي على البيانات المسترجعة
        """
        try:
            # 1. التحقق من وجود تعريف الاستعلام
            if intent not in self.query_definitions:
                logger.warning(f"لا يوجد تعريف للاستعلام للنية: {intent}")
                return {"error": f"لا يوجد تعريف للاستعلام للنية: {intent}"}

            query_def = self.query_definitions[intent]

            # 2. التحقق من الكيانات المطلوبة
            missing_entities = []
            for param in query_def["required_params"]:
                if param not in entities or not entities[param]:
                    missing_entities.append(param)

            if missing_entities:
                logger.warning(f"الكياانات المفقودة للاستعلام: {missing_entities}")
                return {
                    "error": f"الكياانات المفقودة: {', '.join(missing_entities)}",
                    "missing_entities": missing_entities
                }

            # 3. إنشاء مفتاح التخزين المؤقت
            cache_key = self._generate_cache_key(intent, entities)

            # 4. التحقق من التخزين المؤقت
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"تم إرجاع النتائج من التخزين المؤقت للاستعلام: {intent}")
                return cached_result

            # 5. بناء الاستعلام
            query_params = self._build_query_params(intent, entities)

            # 6. تنفيذ الاستعلام
            result = self._execute_query(intent, query_params)

            # 7. تخزين النتائج في التخزين المؤقت
            self._set_cache(cache_key, result)

            logger.info(f"تم تنفيذ الاستعلام بنجاح: {intent}")
            return result

        except Exception as e:
            logger.error(f"فشل في تنفيذ الاستعلام: {str(e)}")
            return {"error": str(e)}

    def _generate_cache_key(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        إنشاء مفتاح فريد للاستعلام للتخزين المؤقت

        Args:
            intent: النية المحددة
            entities: الكيانات المستخرجة

        Returns:
            مفتاح فريد للاستعلام
        """
        # إنشاء نسخة منظمة من الكيانات
        sorted_entities = {k: sorted(v) if isinstance(v, list) else v for k, v in sorted(entities.items())}
        entities_str = json.dumps(sorted_entities, sort_keys=True)

        # إنشاء المفتاح
        cache_key = f"{intent}_{entities_str}"

        return cache_key

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        الحصول على النتائج من التخزين المؤقت

        Args:
            cache_key: مفتاح التخزين المؤقت

        Returns:
            النتائج المخزنة أو None إذا لم تكن موجودة
        """
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # التحقق من انتهاء الصلاحية
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
            else:
                # حذف البيانات المنتهية الصلاحية
                del self.cache[cache_key]

        return None

    def _set_cache(self, cache_key: str, data: Dict[str, Any]):
        """
        تخزين النتائج في التخزين المؤقت

        Args:
            cache_key: مفتاح التخزين المؤقت
            data: البيانات المراد تخزينها
        """
        self.cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }

    def _build_query_params(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        بناء معاملات الاستعلام

        Args:
            intent: النية المحددة
            entities: الكيانات المستخرجة

        Returns:
            قاموس يحتوي على معاملات الاستعلام
        """
        query_params = {}

        if intent in self.query_definitions:
            query_def = self.query_definitions[intent]

            # إضافة المعاملات المطلوبة
            for param in query_def["required_params"]:
                if param in entities:
                    # إذا كانت القائمة، خذ العنصر الأول
                    value = entities[param][0] if isinstance(entities[param], list) else entities[param]
                    query_params[param] = value

            # إضافة المعاملات الاختيارية إذا كانت موجودة
            for param in query_def["optional_params"]:
                if param in entities:
                    value = entities[param][0] if isinstance(entities[param], list) else entities[param]
                    query_params[param] = value

        return query_params

    def _execute_query(self, intent: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        تنفيذ الاستعلام الفعلي

        Args:
            intent: النية المحددة
            query_params: معاملات الاستعلام

        Returns:
            قاموس يحتوي على النتائج
        """
        if intent not in self.query_definitions:
            return {"error": f"لا يوجد تعريف للاستعلام للنية: {intent}"}

        query_def = self.query_definitions[intent]
        endpoint = query_def["endpoint"]
        method = query_def["method"]

        # بناء عنوان URL الكامل
        url = f"{self.api_base_url}{endpoint}"

        # استبدال المعاملات في عنوان URL
        for param, value in query_params.items():
            url = url.replace(f"{{{param}}}", str(value))

        # إعداد رؤوس الطلبات
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept-Language": "ar"  # دعم اللغة العربية
        }

        try:
            # تنفيذ الطلب
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=query_params, timeout=self.timeout)
            else:
                return {"error": f"الطريقة غير المدعومة: {method}"}

            # التحقق من حالة الاستجابة
            if response.status_code == 200:
                result = response.json()

                # تطبيق تعيين الاستجابة إذا كان موجوداً
                if "response_mapping" in query_def:
                    mapped_result = self._map_response(result, query_def["response_mapping"])
                    return mapped_result

                return result
            else:
                logger.error(f"فشل الاستعلام - حالة الاستجابة: {response.status_code}")
                return {
                    "error": f"فشل الاستعلام - حالة الاستجابة: {response.status_code}",
                    "details": response.text
                }

        except requests.exceptions.Timeout:
            logger.error("انتهت مهلة الاستعلام")
            return {"error": "انتهت مهلة الاستعلام"}
        except requests.exceptions.RequestException as e:
            logger.error(f"خطأ في تنفيذ الاستعلام: {str(e)}")
            return {"error": str(e)}

    def _map_response(self, response: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        تطبيق تعيين الاستجابة لتوحيد هيكل البيانات

        Args:
            response: الاستجابة الأصلية
            mapping: تعيين الحقول

        Returns:
            قاموس يحتوي على الاستجابة المعدلة
        """
        mapped_response = {}

        for source_field, target_field in mapping.items():
            if source_field in response:
                mapped_response[target_field] = response[source_field]

        # إضافة الحقول التي لا تحتاج إلى تعيين
        for key, value in response.items():
            if key not in mapping:
                mapped_response[key] = value

        return mapped_response

    def clear_cache(self):
        """
        مسح التخزين المؤقت بالكامل
        """
        self.cache = {}
        logger.info("تم مسح التخزين المؤقت")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        الحصول على معلومات حول التخزين المؤقت

        Returns:
            قاموس يحتوي على معلومات التخزين المؤقت
        """
        return {
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl,
            "cached_keys": list(self.cache.keys())
        }

    def validate_api_connection(self) -> bool:
        """
        التحقق من الاتصال بواجهة برمجة تطبيقات البيانات

        Returns:
            True إذا كان الاتصال ناجحاً، False إذا لم يكن كذلك
        """
        try:
            # إجراء استعلام بسيط للتحقق من الاتصال
            response = requests.get(
                f"{self.api_base_url}/health",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )

            if response.status_code == 200:
                logger.info("تم التحقق من الاتصال بواجهة برمجة تطبيقات البيانات بنجاح")
                return True
            else:
                logger.warning(f"فشل في التحقق من الاتصال - حالة الاستجابة: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"فشل في التحقق من الاتصال: {str(e)}")
            return False
return mapped_response

    def clear_cache(self):
        """مسح التخزين المؤقت"""
        self.cache = {}
        logger.info("تم مسح التخزين المؤقت")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        الحصول على معلومات التخزين المؤقت

        Returns:
            قاموس يحتوي على معلومات التخزين المؤقت
        """
        return {
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl,
            "cached_keys": list(self.cache.keys())
        }
