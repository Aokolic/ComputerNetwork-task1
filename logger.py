import logging
import sys
import os

def setup_logger(log_file: str = 'run_log.txt', name: str = 'reverse_tcp'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger
    
    fmt = logging.Formatter(
        '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_log_file = os.path.join(current_dir, log_file)

    file_handler = logging.FileHandler(absolute_log_file, mode='w', encoding='utf-8')
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger