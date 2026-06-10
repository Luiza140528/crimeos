import os
import time
import random
import logging
import requests
import subprocess
from pathlib import Path
from gtts import gTTS
import imageio_ffmpeg

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("CrimeOS")

CONFIG = {
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "FAL_API_KEY": os.getenv("FAL_API_KEY", ""),
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
}

TEMAS_PT = [
    "Um homem desapareceu e ninguem soube por 20 anos",
    "A mulher que fingiu sua propria morte para escapar",
    "O serial killer que morava ao lado de uma delegacia",
    "O crime que ocorreu em plena transmissao ao vivo",
    "A crianca desaparecida que reapareceu 15 anos depois",
]

TEMAS_EN = [
    "He vanished and nobody knew for 20 years",
    "The woman who faked her own death to escape",
    "The serial killer who lived next to a police station",
    "The crime that happened live on television",
    "The missing child who reappeared 15 years later",
]

def gerar_roteiro(tema, lang="PT"):
    log.info("[1/4] Gerando roteiro")
    if lang == "PT":
        system = """Atue como um roteirista sênior de documentários de True Crime para redes sociais. Você escreverá um roteiro de no máximo 60 segundos com o objetivo de máxima retenção.

REGRAS DE FORMATAÇÃO (CRÍTICAS):
PROIBIDO o uso de hashtags (#) em qualquer parte do texto.
PROIBIDO o uso de asteriscos (**) ou qualquer marcação de negrito/itálico.
O texto deve conter APENAS o conteúdo da narração. Sem títulos, sem introduções de cena, sem notas de autor.
Use apenas pontuação padrão (vírgula, ponto, interrogação).

ESTRUTURA DE STORYTELLING:
O GANCHO (0-5s): Comece com uma afirmação perturbadora ou uma pergunta que crie um vácuo de curiosidade imediato.
O MEIO (5-45s): Apresente os fatos como pistas. Evite datas, nomes burocráticos ou listas. Foque no que é bizarro ou inexplicável. Mantenha frases curtas.
O FECHAMENTO (45-60s): Termine com uma teoria inquietante ou pergunta sobre a motivação. Nunca faça resumo.

TOM DE VOZ: Sombrio, direto, intrigante e profissional."""
    else:
        system = """Act as a senior True Crime documentary scriptwriter for social media. Write a script of maximum 60 seconds with the goal of maximum retention.

FORMATTING RULES (CRITICAL):
NO hashtags (#) anywhere in the text.
NO asterisks (**) or bold/italic markup.
Text must contain ONLY the narration content. No titles, no scene introductions, no author notes.
Use only standard punctuation (comma, period, question mark).

STORYTELLING STRUCTURE:
THE HOOK (0-5s): Start with a disturbing statement or question that creates immediate curiosity.
THE MIDDLE (5-45s): Present facts as clues. Avoid dates, bureaucratic names or lists. Focus on what is bizarre or inexplicable. Keep sentences short.
THE CLOSING (45-60s): Never summarize. End with an unsettling theory or question about the criminal's motivation.

TONE: Dark, direct, intriguing and professional."""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": CONFIG["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 500, "system": system, "messages": [{"role": "user", "content": tema}]},
        timeout=30,
    )
    texto = resp.json()["content"][0]["text"]
    log.info("Roteiro gerado!")
    return texto

def gerar_narracao(texto, lang, output_path):
    log.info("[2/4] Gerando narracao")
    lang_code = "pt" if lang == "PT" else "en"
    tts = gTTS(text=texto, lang=lang_code)
    tts.save(output_path)
    log.info("Narracao salva!")
    return output_path

def gerar_imagem(prompt, output_path):
    log.info("[3/4] Gerando imagem")
    resp = requests.post(
        "https://fal.run/fal-ai/flux/schnell",
        headers={"Authorization": "Key " + CONFIG["FAL_API_KEY"], "Content-Type": "application/json"},
        json={"prompt": prompt + ", cinematic dark, dramatic lighting, crime scene, 4k", "image_size": "portrait_4_3", "num_inference_steps": 4, "num_images": 1},
        timeout=60,
    )
    url = resp.json()["images"][0]["url"]
    img = requests.get(url, timeout=30).content
    Path(output_path).write_bytes(img)
    log.info("Imagem salva!")
    return output_path

def montar_video(audio_path, img_path, output_path):
    log.info("[4/4] Montando video")
    result = subprocess.run([
        ffmpeg_path, "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-shortest",
        "-movflags", "+faststart",
        output_path
    ], capture_output=True)
    if result.returncode != 0:
        raise Exception("FFmpeg erro: " + result.stderr.decode()[-300:])
    log.info("Video montado!")
    return output_path

def enviar_video(video_path, mensagem):
    log.info("Enviando video")
    token = CONFIG["TELEGRAM_BOT_TOKEN"]
    chat_id = CONFIG["TELEGRAM_CHAT_ID"]
    with open(video_path, "rb") as f:
        requests.post(
            "https://api.telegram.org/bot" + token + "/sendVideo",
            data={"chat_id": chat_id, "caption": mensagem},
            files={"video": f},
            timeout=120,
        )
    log.info("Video enviado!")

def enviar_msg(mensagem):
    token = CONFIG["TELEGRAM_BOT_TOKEN"]
    chat_id = CONFIG["TELEGRAM_CHAT_ID"]
    requests.post(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        json={"chat_id": chat_id, "text": mensagem},
        timeout=15,
    )

def rodar(lang="PT"):
    log.info("CrimeOS iniciando " + lang)
    temas = TEMAS_PT if lang == "PT" else TEMAS_EN
    tema = random.choice(temas)
    work_dir = "/tmp/crimeos_" + lang
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    try:
        roteiro = gerar_roteiro(tema, lang)
        audio = work_dir + "/audio.mp3"
        gerar_narracao(roteiro, lang, audio)
        imagem = work_dir + "/imagem.jpg"
        gerar_imagem(tema, imagem)
        video = work_dir + "/video.mp4"
        montar_video(audio, imagem, video)
        enviar_video(video, "Video pronto " + lang + " - Tema: " + tema)
        log.info("Concluido!")
    except Exception as e:
        log.error("Erro: " + str(e))
        enviar_msg("Erro " + lang + ": " + str(e))

if __name__ == "__main__":
    while True:
        rodar("PT")
        rodar("EN")
        time.sleep(3600)
