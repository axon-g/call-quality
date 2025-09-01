"""
Extract features from audio

"""
import logging
import os

LOG = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BLD_DIR = os.path.join(SCRIPT_DIR, "..", "build")

SHOPPERS_AUDIO_ROOT = os.getenv("SHOPPERS_AUDIO_ROOT")
if SHOPPERS_AUDIO_ROOT is None:
    raise ValueError("Cannot find env.var 'SHOPPERS_AUDIO_ROOT' -> create/check '.env' file in the script's dir!")


def dev() -> None:
    pass


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s", level=logging.DEBUG)
    dev()
