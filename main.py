import os
import requests
import time
from robot import rodar

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT = os.getenv("TELEGRAM_CHAT_ID", "")

requests.post(
    "https://api.telegram.org/bot" + TOKEN + "/sendMessage",
    json={"chat_id": CHAT, "text": "Robo iniciando..."},
    timeout=15,
)

rodar("PT")
time.sleep(10)
rodar("EN")

requests.post(
    "https://api.telegram.org/bot" + TOKEN + "/sendMessage",
    json={"chat_id": CHAT, "text": "Robo finalizado!"},
    timeout=15,
)
