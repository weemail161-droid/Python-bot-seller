# trc20_checker.py - يعمل بـ API Key لتحسين الأداء والاستقرار
import os
import requests

def verify_tron_txid(txid, wallet_address, min_amount):
    """
    تحقق من أن TXID يحتوي على تحويل USDT إلى محفظتك باستخدام API Key
    """
    try:
        # قراءة API Key من البيئة
        api_key = os.getenv("TRON_API_KEY", "").strip()
        if not api_key:
            print("[API] ⚠️ لم يتم تعيين TRON_API_KEY في config.env")
            return False

        # رابط التحقق من العملية
        url = f"https://api.trongrid.io/v1/transactions/{txid}"

        # إضافة API Key في الـ Header
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "TRON-PRO-API-KEY": api_key  # ← المفتاح السري
        }

        # إرسال الطلب
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"[API] ❌ خطأ HTTP: {response.status_code} - {response.text[:100]}")
            return False

        data = response.json()

        # التحقق من وجود العقد
        contract = data.get("raw_data", {}).get("contract", [])
        if not contract:
            return False

        if contract[0].get("type") != "TriggerSmartContract":
            return False

        value = contract[0]["parameter"]["value"]
        to_addr = value.get("to_address", "").lower()
        token_id = value.get("token_id")
        amount = float(value.get("amount", "0")) / 1_000_000  # USDT
        from_addr = value.get("owner_address", "").lower()

        # التحقق النهائي
        if (to_addr == wallet_address.lower() and
            token_id == "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t" and
            amount >= min_amount and
            from_addr != wallet_address.lower()):
            return True

        return False

    except Exception as e:
        print(f"[Verify] خطأ غير متوقع: {e}")
        return False