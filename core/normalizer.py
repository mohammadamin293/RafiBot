# core/normalizer.py
import re

def normalize_text(text: str) -> str:
    """نرمال‌سازی متن برای جلوگیری از دور زدن فیلترها"""
    # تبدیل حروف عربی به فارسی
    text = text.replace('ي', 'ی').replace('ك', 'ک')
    
    # حذف نیم‌فاصله و فاصله‌های نامرئی
    text = text.replace('\u200c', '').replace('\u200d', '').replace('\u200b', '')
    
    # حذف کاراکترهای خاص که کاربران برای دور زدن استفاده می‌کنند (مثل نقطه گذاشتن بین حروف)
    text = re.sub(r'[._-]', '', text)
    
    # تبدیل به حروف کوچک انگلیسی
    return text.lower()