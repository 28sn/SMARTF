from twilio.rest import Client

# Twilio credentials
account_sid = 'AC40e71835d9a7576a5f1cad727ce59566'
auth_token = 'aaf699b95cbd21a0593ea554aa25d9b5'
twilio_number = '+19785475826'
to_number = '+96891137278'

# اسم الملف الخاص بسلة التسوق
SHOPPING_FILE = "shopping_cart.txt"

# دالة لقراءة سلة التسوق
def read_cart():
    try:
        with open(SHOPPING_FILE, "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        cart = {}
        for item in lines:
            item = item.strip().lower()
            if item:
                cart[item] = cart.get(item, 0) + 1
        return [f"{name} × {qty}" for name, qty in cart.items()]
    except FileNotFoundError:
        return []

# توليد نص الرسالة
def generate_message():
    cart = read_cart()
    if not cart:
        return "🛒 سلة التسوق فارغة"
    msg = "🛍 قائمة التسوق:\n" + "\n".join(f"- {item}" for item in cart)
    return msg[:150]  # الحد المسموح لرسائل SMS

# إرسال الرسالة
def send_sms():
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=generate_message(),
        from_=twilio_number,
        to=to_number
    )
    print(f"✅ تم إرسال سلة التسوق! SID: {message.sid}")

# للتشغيل المباشر
if __name__ == "__main__":
    send_sms()
