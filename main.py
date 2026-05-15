import logging
import time
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("CrimeOS")
log.info("Iniciando...")
from robot import rodar
rodar("PT")
time.sleep(10)
rodar("EN")
log.info("Fim!")




