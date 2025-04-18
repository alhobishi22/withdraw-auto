import os
import json
import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskerAutomation:
    """
    فئة للتعامل مع أتمتة التحويلات باستخدام تطبيق Tasker
    """
    
    def __init__(self, tasker_endpoint: str = None):
        """
        تهيئة الفئة مع نقطة نهاية Tasker
        
        :param tasker_endpoint: عنوان URL لواجهة برمجة تطبيقات Tasker
        """
        self.tasker_endpoint = tasker_endpoint or os.getenv("TASKER_ENDPOINT", "http://localhost:8080/tasker")
        self.timeout = 30  # مهلة الاتصال بالثواني
    
    def send_transfer_to_tasker(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        إرسال بيانات التحويل إلى Tasker لتنفيذ العملية تلقائياً
        
        :param transfer_data: بيانات التحويل (المحفظة، الرقم، المبلغ، العملة، إلخ)
        :return: نتيجة العملية
        """
        try:
            # تحضير البيانات للإرسال إلى Tasker
            payload = {
                "action": "transfer",
                "wallet_name": transfer_data.get("wallet_name"),
                "wallet_type": self._get_wallet_type(transfer_data.get("wallet_name")),
                "recipient_number": transfer_data.get("recipient_number"),
                "amount": transfer_data.get("amount"),
                "currency": transfer_data.get("local_currency"),
                "transfer_id": transfer_data.get("transfer_id"),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"إرسال طلب تحويل إلى Tasker: {transfer_data.get('transfer_id')}")
            
            # إرسال البيانات إلى Tasker
            response = requests.post(
                self.tasker_endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"تم استلام رد من Tasker: {result}")
                return result
            else:
                logger.error(f"خطأ في الاتصال بـ Tasker: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"خطأ في الاتصال: {response.status_code}",
                    "transfer_id": transfer_data.get("transfer_id")
                }
                
        except requests.RequestException as e:
            logger.error(f"خطأ في طلب Tasker: {e}")
            return {
                "success": False,
                "error": f"خطأ في الاتصال: {str(e)}",
                "transfer_id": transfer_data.get("transfer_id")
            }
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {e}")
            return {
                "success": False,
                "error": f"خطأ غير متوقع: {str(e)}",
                "transfer_id": transfer_data.get("transfer_id")
            }
    
    def _get_wallet_type(self, wallet_name: str) -> str:
        """
        تحديد نوع المحفظة بناءً على اسمها
        
        :param wallet_name: اسم المحفظة
        :return: نوع المحفظة للاستخدام في Tasker
        """
        wallet_types = {
            "جوالي": "jawali",
            "كريمي": "kreemy",
            "كاش": "cash",
            "ون كاش": "onecash",
            "جيب": "jaib"
        }
        
        # تنظيف اسم المحفظة من المسافات الزائدة
        clean_name = wallet_name.strip() if wallet_name else ""
        
        # البحث عن النوع المناسب
        for name, wallet_type in wallet_types.items():
            if name in clean_name:
                return wallet_type
        
        # إرجاع القيمة الافتراضية إذا لم يتم العثور على تطابق
        return "unknown"
    
    def handle_tasker_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        معالجة الاستدعاء العكسي من Tasker بعد محاولة التحويل
        
        :param callback_data: بيانات الاستدعاء العكسي من Tasker
        :return: نتيجة المعالجة
        """
        try:
            transfer_id = callback_data.get("transfer_id")
            success = callback_data.get("success", False)
            error_message = callback_data.get("error")
            
            if not transfer_id:
                logger.error("معرف التحويل مفقود في بيانات الاستدعاء العكسي")
                return {
                    "success": False,
                    "error": "معرف التحويل مفقود"
                }
            
            logger.info(f"استلام استدعاء عكسي من Tasker للتحويل {transfer_id}: نجاح={success}")
            
            if success:
                # تم التحويل بنجاح
                result = {
                    "success": True,
                    "transfer_id": transfer_id,
                    "message": "تم التحويل بنجاح",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # فشل التحويل
                result = {
                    "success": False,
                    "transfer_id": transfer_id,
                    "error": error_message or "حدث خطأ أثناء التحويل",
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الاستدعاء العكسي: {e}")
            return {
                "success": False,
                "error": f"خطأ في معالجة الاستدعاء العكسي: {str(e)}"
            }
