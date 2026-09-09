# core/normalizer.py
import re

def normalize_text(text: str) -> str:
    """نرمال‌سازی متن برای جلوگیری از دور زدن فیلترها"""
    # تبدیل حروف عربی به فارسی
    arabic_to_persian = {
        'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 'ؤ': 'و', 'ئ': 'ی',
        'إ': 'ا', 'أ': 'ا', 'آ': 'ا', 'ى': 'ی'
    }
    for arabic, persian in arabic_to_persian.items():
        text = text.replace(arabic, persian)
    
    # تبدیل اعداد عربی به فارسی
    arabic_numbers = {
        '٠': '۰', '١': '۱', '٢': '۲', '٣': '۳', '٤': '۴',
        '٥': '۵', '٦': '۶', '٧': '۷', '٨': '۸', '٩': '۹'
    }
    for arabic, persian in arabic_numbers.items():
        text = text.replace(arabic, persian)
    
    # حذف نیم‌فاصله و فاصله‌های نامرئی
    text = text.replace('\u200c', '').replace('\u200d', '').replace('\u200b', '')
    
    # حذف کاراکترهای خاص برای دور زدن
    text = re.sub(r'[._-]', '', text)
    
    # تبدیل به حروف کوچک انگلیسی
    return text.lower()