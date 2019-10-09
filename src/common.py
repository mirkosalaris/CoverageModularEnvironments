import logging

__all__ = ["logger"]


# SET THESE TWO #
stream_level = 1  # 0 for debug, 1 for info, 2 for warning, 3 for critical
file_level = 0  # 0 for debug, 1 for info, 2 for warning, 3 for critical
#################

LOGGER_NAME = "main_logger"
LOG_FILENAME = "info.log"
LEVELS = [logging.DEBUG, logging.INFO, logging.WARNING, logging.CRITICAL]

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LEVELS[0])  # set global level. It must be the lowest possible

stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler(LOG_FILENAME)

stream_handler.setLevel(LEVELS[stream_level])
file_handler.setLevel(LEVELS[file_level])

stream_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler.setFormatter(stream_formatter)
file_handler.setFormatter(file_formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)