import logging
import time
import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("test")

TOKEN = "8689399024:AAG9yslBw6IakjWW6GGePym39GJkFvk3am4"
CHAT = "8615185217"

log.info("Testando Telegram...")
r = requests.post(
    "https://api.telegram.org/bot" + TOKEN + "/sendMessage",
    json={"chat_id": CHAT, "text": "Robo rodando! Teste direto."},
    timeout=15,
)
log.info("Status: " + str(r.status_code))
log.info("Resposta: " + r.text[:100])




