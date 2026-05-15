
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("CrimeOS")

log.info("Iniciando CrimeOS...")

from robot import rodar
import time

log.info("Rodando PT...")
rodar("PT")
time.sleep(10)
log.info("Rodando EN...")
rodar("EN")
log.info("Finalizado!")



