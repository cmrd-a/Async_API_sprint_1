import logging
import sys
from logging import StreamHandler
from logging.handlers import RotatingFileHandler


logger = logging.getLogger('etl_logger')
logger.setLevel(logging.INFO)

stream_handler = StreamHandler(stream=sys.stdout)
logger.addHandler(stream_handler)

file_handler = RotatingFileHandler(filename='etl_logs.log', maxBytes=2000000)
logger.addHandler(file_handler)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
