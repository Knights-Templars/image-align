import logging
from pathlib import Path

def setup_logger(log_dir: Path, level=logging.INFO):

    logger = logging.getLogger("imagealign")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # this will write to a file
    file_handler = logging.FileHandler(log_dir / "log.INFO")
    file_handler.setFormatter(formatter)

    # this will write to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # pass these handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


    return logger





