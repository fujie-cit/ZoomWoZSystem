import logging

logging.basicConfig(
    filename="system.log", 
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s.%(funcName)s %(message)s",
    datefmt="%Y/%m/%dT%H:%M:%S",
    level=logging.DEBUG)
logging.debug("hogehogehoge")

def func():
    logging.debug("XXXXX")

func()
