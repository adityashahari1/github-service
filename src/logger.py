# Author: Aditya Shahari
# Contributor(s):

import logging
import sys

logger = logging.getLogger("issues-proxy")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(console_handler)
