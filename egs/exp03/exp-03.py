"""
Extract features from audio

"""
import logging
import os
import numpy as np
import librosa

LOG = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BLD_DIR = os.path.join(SCRIPT_DIR, "..", "build")

SHOPPERS_AUDIO_ROOT = os.getenv("SHOPPERS_AUDIO_ROOT")
if SHOPPERS_AUDIO_ROOT is None:
    raise ValueError("Cannot find env.var 'SHOPPERS_AUDIO_ROOT' -> create/check '.env' file in the script's dir!")


def iter_mp3():
    for root, _, fnames in os.walk(SHOPPERS_AUDIO_ROOT):
        for fname in [f for f in fnames if f.endswith(".mp3")]:
            yield os.path.join(root, fname)


def analyze_one(mp3_file, n_fft: int = 400, shift: int = -1) -> np.ndarray:
    y, hz = librosa.load(mp3_file, sr=None, mono=False)
    shift = int(n_fft / 2 if shift < 0 else shift)
    D = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=shift))
    ax_time = librosa.times_like(D, sr=hz)

    S, phase = librosa.magphase(D)  # 複素数を強度と位相へ変換
    dB = librosa.amplitude_to_db(S)  # 強度をdb単位へ変換
    return dB.transpose(), y.shape[0]


def dev(n_fft: int, n_shift: int) -> None:
    n_mp3 = 0
    running_off = 0
    for fpath_mp3 in iter_mp3():
        LOG.debug("Processing %d. %s", n_mp3, fpath_mp3)
        n_mp3 += 1
        ffts, n_sample = analyze_one(fpath_mp3, n_fft=n_fft, shift=n_shift)




if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s", level=logging.DEBUG)
    dev()
