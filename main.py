import logging
import time
from robot import rodar

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("CrimeOS")
log.info("Iniciando...")
rodar("PT")
time.sleep(10)
rodar("EN")
log.info("Fim!")
