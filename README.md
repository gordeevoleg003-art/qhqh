# Telegram Game Bot

Игровой бот: рулетка, кейсы, дуэли, семьи, аукционы, AZ.

## Деплой на Render

1. Форкни репозиторий
2. render.com → New → Web Service → подключи GitHub
3. Environment Variables:
   - BOT_TOKEN
   - ADMIN_ID
   - CHAT_ID
   - DATA_DIR = /data
4. Deploy

## Запуск локально

```bash
export BOT_TOKEN="8703857750:AAGWCvf_kgaMyigpNSDfwyLFzS2Sl8ppLig"
export ADMIN_ID="6548175188"
export CHAT_ID="-1001234567890"
python bot_cloud.py
