# Telegram Subscription Bot

Ye bot screenshot wale flow ka ready-to-run starter hai:

/start
→ 🧾 Buy Subscription
→ Group select
→ VIP stock plans
→ QR payment
→ ✅ Paid — Check Payment
→ Admin payment approve karta hai
→ Bot one-time join link bhejta hai

## 1. Files
- `bot.py` — main bot
- `requirements.txt` — dependency
- `.env.example` — settings example
- `qr.png` — apna UPI/Paytm QR yahan rakhein

## 2. Run
Python 3.10+ install karein:

```bash
pip install -r requirements.txt
```

Environment variables set karein:

```bash
BOT_TOKEN="BotFather token"
ADMIN_ID="Aapka Telegram numeric user ID"
VIP_CHAT_ID="@your_channel"
TANGO_CHAT_ID="@your_channel"
SNAP_CHAT_ID="@your_channel"
VILAYATI_CHAT_ID="@your_channel"
```

Phir:

```bash
python bot.py
```

## 3. Telegram setup
Har target channel/group me bot ko administrator banayein aur invite users/create invite links ki permission dein.

## 4. Payment verification
Is starter me UPI QR payment **manual admin approval** se verify hoti hai.
User `Paid — Check Payment` dabata hai; admin ko order ID milti hai.

Admin:
```text
/approve 123
```

Approve hone par bot target channel/group ka one-time invite link banakar user ko bhejta hai.

## Important
QR image ko `qr.png` naam se project folder me rakhein.

Automatic UPI payment verification ke liye payment gateway/webhook (jaise Razorpay/PayU/Cashfree) alag se configure karna hoga. QR image se Telegram bot khud bank payment confirm nahi kar sakta.
