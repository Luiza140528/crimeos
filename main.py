from robot import processar_video
import random

temas_pt = [
    "A mulher que fingiu a propria morte para escapar",
    "O desaparecimento no elevador que nunca foi explicado",
]

temas_en = [
    "The man who vanished without a trace for 20 years",
    "The unsolved murder that changed a small town",
]

processar_video("pt", random.choice(temas_pt))
processar_video("en", random.choice(temas_en))
