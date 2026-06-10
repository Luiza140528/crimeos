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
