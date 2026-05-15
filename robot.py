import os
import time
import random
import logging
import requests
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("CrimeOS")

CONFIG = {
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY", ""),
    "FAL_API_KEY": os.getenv("FAL_API_KEY", ""),
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
    log.info(f"[1/4] Gerando roteiro: {tema}")
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
    log.info("[2/4] Gerando narracao...")
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

def gerar_imagem(prompt, output_path):
    log.info(f"[3/4] Gerando imagem...")
    resp = requests.post(
        "https://fal.run/fal-ai/flux/schnell",
        headers={"Authorization": f"Key {CONFIG['FAL_API_KEY']}", "Content-Type": "application/json"},
        json={"prompt": f"{prompt}, cinematic dark atmosphere, dramatic lighting, crime scene, 4k", "image_size": "portrait_4_3", "num_inference_steps": 4, "num_images": 1},
        timeout=60,
    )
    url = resp.json()["images"][0]["url"]
    img = requests.get(url, timeout=30).content
    Path(output_path).write_bytes(img)
    log.info("    Imagem salva!")
    return output_path

def montar_video(audio_path, img_path, output_path):
    log.info("[4/4] Montando video...")
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", "-movflags", "+faststart",
        output_path
    ], capture_output=True, check=True)
    log.info("    Video montado!")
    return output_path

def enviar_telegram_video(video_path, mensagem):
    log.info("Enviando video no Telegram...")
    token = CONFIG["TELEGRAM_BOT_TOKEN"]
    chat_id = CONFIG["TELEGRAM_CHAT_ID"]
    with open(video_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendVideo",
            data={"chat_id": chat_id, "caption": mensagem},
            files={"video": f},
            timeout=120,
        )
    log.info("    Video enviado!")

def enviar_telegram(mensagem):
    token = CONFIG["TELEGRAM_BOT_TOKEN"]
    chat_id = CONFIG["TELEGRAM_CHAT_ID"]
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": mensagem},
        timeout=15,
    )

def rodar_pipeline(lang="PT"):
    log.info(f"\nCrimeOS iniciando [{lang}]...")
    temas = TEMAS_PT if lang == "PT" else TEMAS_EN
    tema = random.choice(temas)
    work_dir = f"/tmp/crimeos_{lang}"
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    try:
        roteiro = gerar_roteiro(tema, lang)
        audio_path = f"{work_dir}/narracao.mp3"
        gerar_narracao(roteiro, lang, audio_path)
        img_path = f"{work_dir}/imagem.jpg"
        gerar_imagem(tema, img_path)
        video_path = f"{work_dir}/video.mp4"
        montar_video(audio_path, img_path, video_path)
        enviar_telegram_video(video_path, f"
        pronto [{lang}]!\n\nTema: {tema}\n\nResponda SIM para aprovar ou NAO para rejeitar.")
        log.info("Pipeline concluido!")
    except Exception as e:
        log.error(f"Erro: {e}")
        enviar_telegram(f"Erro no pipeline [{lang}]: {e}")

if __name__ == "__main__":
    for lang in ["PT", "EN"]:
        rodar_pipeline(lang)
        time.sleep(10)Video pronto [{lang}]!\n\nTema: {tem
