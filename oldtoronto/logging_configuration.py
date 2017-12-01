import datetime
import logging
import os


def configure_logging(log_file):
    logger = logging.getLogger('')

    # create file handler which logs even debug messages
    logger.setLevel(logging.DEBUG)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')
    timestamped_log_file = f'{log_file}.{timestamp}'

    # create file handler which logs even debug messages
    filehandler = logging.FileHandler(timestamped_log_file)
    filehandler.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    filehandler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(filehandler)
    logger.addHandler(console_handler)

    # Make log_file a hard link to the new timestamped log file.
    if os.path.exists(log_file):
        os.remove(log_file)
    os.link(timestamped_log_file, log_file)
