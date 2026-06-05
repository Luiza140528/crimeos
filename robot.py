import os
import asyncio
import random
import subprocess
import requests
import logging
import time
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
FAL_API_KEY = os.environ["FAL_API_KEY"]

TEMAS_PT = [
    "A mulher que fingiu a propria morte para escapar",
    "O desaparecimento no elevador que nunca foi explicado",
    "A carta deixada pelo assassino que nunca pegaram",
    "O codigo misterioso encontrado em um corpo",
    "A casa que escondia um segredo por 30 anos"
]

TEMAS_EN = [
    "The man who vanished without a trace for 20 years",
    "The unsolved murder that changed a small town",
    "The mysterious phone call before the disappearance",
    "The evidence hidden in plain sight",
    "The confession that never came"
]

def gerar_roteiro(tema, idioma):
    prompt = f"Voce e roteirista de true crime para TikTok. Escreva um roteiro de 60 segundos para o tema: {tema}. Divida em [CENA 1], [CENA 2], [CENA 3]. Linguagem coloquial. Finalize com pergunta."
    headers = {"x-api-key": ANTHROPIC_API_KEY, "content-type": "application/json", "anthropic-version": "2023-06-01"}
    data = {"model": "claude-haiku-4-5-20251001", "max_tokens": 500, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post("https://api.anthropic.com/v1/messages", json=data, headers=headers)
    response.raise_for_status()
    roteiro = response.json()["content"][0]["text"]
    logger.info("Roteiro gerado")
    return roteiro

def extrair_blocos(roteiro):
    blocos = re.split(r'\[CENA \d+\]', roteiro)
    blocos = [b.strip() for b in blocos if b.strip()]
    if not blocos:
        blocos = [roteiro]
    while len(blocos) < 3:
        blocos.append(blocos[-1])
    return blocos[:3]

async def gerar_audio_edge(texto, idioma, output_path="audio.mp3"):
    import edge_tts
    voz = "pt-BR-AntonioNeural" if idioma == "pt" else "en-US-JennyNeural"
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(output_path)
    logger.info("Audio salvo")
    return output_path

def gerar_imagem_fal(prompt_tema, nome_arquivo):
    url = "https://fal.run/fal-ai/flux/schnell"
    payload = {"prompt": prompt_tema + ", cinematic dark, dramatic lighting, crime scene, 4k", "image_size": "portrait_4_3"}
    headers = {"Authorization": "Key " + FAL_API_KEY, "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    image_url = response.json()["images"][0]["url"]
    img_data = requests.get(image_url).content
    with open(nome_arquivo, "wb") as f:
        f.write(img_data)
    logger.info("Imagem salva: " + nome_arquivo)
    return nome_arquivo

def formatar_tempo(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    millis = int((segundos % 1) * 1000)
    return f"{horas:02d}:{minutos:02d}:{segs:02d},{millis:03d}"

def gerar_legendas_srt(blocos, duracao_total):
    duracao_por_bloco = duracao_total / len(blocos)
    srt_lines = []
    indice = 1
    tempo_atual = 0.0
    for i, bloco in enumerate(blocos):
        frases = bloco.replace('\n', ' ').split('. ')
        duracao_frase = duracao_por_bloco / len(frases) if frases else duracao_por_bloco
        for frase in frases:
            if not frase.strip():
                continue
            inicio = tempo_atual
            fim = inicio + duracao_frase
            srt_lines.append(str(indice))
            srt_lines.append(formatar_tempo(inicio) + " --> " + formatar_tempo(fim))
            srt_lines.append(frase.strip())
            srt_lines.append("")
            indice += 1
            tempo_atual = fim
        tempo_atual = (i + 1) * duracao_por_bloco
    with open("legendas.srt", "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    logger.info("Legendas geradas")
    return "legendas.srt"

def montar_video(imagens, audio_path, legendas_srt, output_path, duracao_total):
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    duracao_por_img = duracao_total / len(imagens)
    with open("concat.txt", "w") as f:
        for img in imagens:
            f.write("file '" + img + "'\n")
            f.write("duration " + str(duracao_por_img) + "\n")
    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0", "-i", "concat.txt",
        "-i", audio_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,subtitles=legendas.srt:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Fontname=Arial'",
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    logger.info("Video montado")
    return output_path

def enviar_telegram(video_path, legenda_texto):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendVideo"
    with open(video_path, "rb") as video:
        files = {"video": video}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": legenda_texto}
        response = requests.post(url, files=files, data=data)
    response.raise_for_status()
    logger.info("Video enviado")

def processar_video(idioma, tema):
    try:
        logger.info("Iniciando " + idioma.upper() + ": " + tema)
        roteiro = gerar_roteiro(tema, idioma)
        blocos = extrair_blocos(roteiro)
        texto_audio = " ".join(blocos)
        audio_path = asyncio.run(gerar_audio_edge(texto_audio, idioma))
        imagens = []
        for i, bloco in enumerate(blocos):
            img_name = "cena_" + str(i) + "_" + str(int(time.time())) + ".jpg"
            gerar_imagem_fal(bloco[:100], img_name)
            imagens.append(img_name)
        duracao_total = 60
        legendas_srt = gerar_legendas_srt(blocos, duracao_total)
        video_output = "video_" + idioma + "_" + str(int(time.time())) + ".mp4"
        montar_video(imagens, audio_path, legendas_srt, video_output, duracao_total)
        enviar_telegram(video_output, "Video pronto " + idioma.upper() + " - " + tema)
        for f in imagens + [audio_path, legendas_srt, video_output, "concat.txt"]:
            if os.path.exists(f):
                os.remove(f)
        logger.info("Concluido " + idioma)
        return True
    except Exception as e:
        logger.error("Erro " + idioma + ": " + str(e))
        try:
            requests.post(
                "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": "Erro " + idioma + ": " + str(e)[:200]}
            )
        except:
            pass
        return False

if __name__ == "__main__":
    logger.info("CrimeOS iniciado. Aguardando 60s...")
    time.sleep(60)
    while True:
        tema_pt = random.choice(TEMAS_PT)
        tema_en = random.choice(TEMAS_EN)
        processar_video("pt", tema_pt)
        time.sleep(30)
        processar_video("en", tema_en)
        logger.info("Ciclo completo. Aguardando 1 hora...")
        time.sleep(3600)
