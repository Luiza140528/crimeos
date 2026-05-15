import os
import json
import time
import random
import logging
import requests
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("CrimeOS")

CONFIG = {
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY", ""),
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
    "VOICE_ID_PT": os.getenv("VOICE_ID_PT", "pNInz6obpgDQGcFmaJgB"),
    "VOICE_ID_EN": os.getenv("VOICE_ID_EN", "EXAVITQu4vr4xnSDxMaL"),
}

TEMAS_PT = [
    "Um homem desapareceu e ninguém soube por 20 anos",
    "A mulher que fingiu sua própria morte para escapar",
    "O serial killer que morava ao lado de uma delegacia",
    "O crime que ocorreu em plena transmissão ao vivo",
    "A criança desaparecida que reapareceu 15 anos depois",
]

TEMAS_EN = [
    "He vanished and nobody knew for 20 years",
    "The woman who faked her own death to escape",
    "The serial killer who lived next to a police station",
    "The crime that happened live on television",
    "The missing child who reappeared 15 years later",
]

def gerar_roteiro(tema, lang="PT"):
    log.info(f"[1/3] Gerando roteiro: {tema}")
    system = "Voce e roteirista de true crime para YouTube Shorts. Crie um roteiro de 60 segundos sobre o tema. Responda so com o texto da narracao, sem explicacoes."
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": CONFIG["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 500, "system": system, "messages": [{"role": "user", "content": tema}]},
        timeout=30,
    )
    texto = resp.json()["content"][0]["text"]
    log.info("    Roteiro gerado!")
    return texto

def gerar_narracao(texto, lang, output_path):
    log.info("[2/3] Gerando narracao...")
    voice_id = CONFIG["VOICE_ID_PT"] if lang == "PT" else CONFIG["VOICE_ID_EN"]
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": CONFIG["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
        json={"text": texto, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}},
        timeout=60,
    )
    Path(output_path).write_bytes(resp.content)
    log.info("    Narracao salva!")
    return output_path

def enviar_telegram(mensagem):
    log.info("[3/3] Enviando Telegram...")
    token = CONFIG["TELEGRAM_BOT_TOKEN"]
    chat_id = CONFIG["TELEGRAM_CHAT_ID"]
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": mensagem},
        timeout=15,
    )
    log.info("    Enviado!")

def rodar_pipeline(lang="PT"):
    log.info(f"\nCrimeOS iniciando [{lang}]...")
    temas = TEMAS_PT if lang == "PT" else TEMAS_EN
    tema = random.choice(temas)
    roteiro = gerar_roteiro(tema, lang)
    work_dir = f"/tmp/crimeos_{lang}"
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    audio_path = f"{work_dir}/narracao.mp3"
    try:
        gerar_narracao(roteiro, lang, audio_path)
        enviar_telegram(f"Roteiro pronto [{lang}]!\n\nTema: {tema}\n\n{roteiro[:300]}...\n\nNarracao gerada!")
    except Exception as e:
        log.error(f"Erro na narracao: {e}")
        enviar_telegram(f"Roteiro pronto [{lang}]!\n\nTema: {tema}\n\n{roteiro[:300]}...\n\nErro na narracao: {e}")
    log.info("Pipeline concluido!")

if __name__ == "__main__":
    for lang in ["PT", "EN"]:
        rodar_pipeline(lang)
        time.sleep(10)
