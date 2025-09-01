"""
Check zero-regions in in-domain real audio.

Discover SHOPPERS audio -> MP3
"""
import datetime
import os
import sys
import logging
from typing import List, Tuple

import numpy as np
import librosa


class AudioFileError(Exception):
    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f'Audio file {filename} failed with reason: {reason}')

    def __str__(self) -> str:
        return f'Audio file {self.filename} failed with reason: {self.reason}'





LOG = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BLD_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "build"))

MP3_ROOT = os.getenv("MP3_DIR")
if MP3_ROOT is None:
    raise ValueError("Cannot find env.var 'MP3_ROOT' -> create/check '.env' file in the script's dir!")
if not os.path.isdir(MP3_ROOT):
    raise ValueError("Cannot find MP3 dir at: %s", MP3_ROOT)


class Audio:
    def __init__(self, mp3_file, off: int = -1, size: int = -1):
        self.fpath = mp3_file
        self.off = off
        self.size = size


def iter_mp3():
    for root, _, fnames in os.walk(MP3_ROOT):
        for fname in [f for f in fnames if f.endswith(".wav")]:
            yield os.path.join(root, fname)




def find_zero_gaps(audio_file, min_dur_ms: int = 20) -> List[Tuple[float, int]]:
    """
    Finds zero-regions in an audio file.

    :param audio_file:
    :param min_dur_ms:
    :return:  (1) (2) (3) sample size of audio
    """
    y, hz = librosa.load(audio_file, sr=None, mono=False)
    if y.shape[0] == 0:
        raise AudioFileError(audio_file, "Audio file is empty")

    values, counts = np.unique(y, return_counts=True)
    index = np.argmax(counts)
    mode = values[index]

    # threshold: min number of samples in span
    min_frame = int(np.ceil((min_dur_ms/1000) * hz))

    def find_spans(ixs: np.ndarray):
        """
        Find  continuous ranges  0 2 4 5 6 7 8
                                     ^^^^^^^^^
        :param ixs:
        :return:
        """
        if ixs.shape[0] == 0:
            return []
        spans = []
        span_len = 0
        span_start = ixs[0]

        for iix, ix in enumerate(ixs):
            if ixs[iix] == ixs[iix-1] + 1:  # current index == prev + 1
                span_len += 1
            else:
                spans.append((int(span_start), span_len))
                span_start = ix
                span_len = 1
        return spans

    # ixs_zero = np.where(np.diff(y) == 0)[0] + 1
    ixs_abs_zero = np.where(y==0)[0]
    gaps_abs_zero = find_spans(ixs_abs_zero)

    # almost zero
    smallest_val = min(np.abs(y[y!=0]))
    ixs_near_zero = np.where(np.abs(y) <= smallest_val)[0]
    gaps_almost_zero = find_spans(ixs_near_zero)

    filtered_abs_zero = [(*g, 0)  for g in gaps_abs_zero if g[1] > min_frame]

    # filtered_near_zero = [g  for g in gaps_almost_zero if g[1] > thresh]
    filtered_near_zero = []
    for off, sz in gaps_almost_zero:
        if sz < min_frame:
            continue
        mean_amp = np.sum(np.abs(y[off:(off + sz)])) / sz
        filtered_near_zero.append((off, sz, mean_amp))
# TODO: nan & negative

    return filtered_abs_zero, filtered_near_zero, y.shape[0]



def run():
    bname = os.path.splitext(os.path.basename(__file__))[0]
    ts = datetime.datetime.now().strftime("run-%Y%m%d_%H%M")
    dpath_out = os.path.join(BLD_DIR, bname, ts)
    os.makedirs(dpath_out, exist_ok=True)

    fpath_stats = os.path.join(dpath_out, "sil-gap-stats.csv")
    sink = open(fpath_stats, "w", encoding="utf-8")
    sink.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format("uid", "GIM", "direction", "zero", "span.off", "span.size", "span.amp", "sample.size"))

    n_mp3 = 0
    for fpath_mp3 in iter_mp3():
        n_mp3 += 1

        # if "20250828-100407-99000000230000001170-GOUT00000023902001-out" not in fpath_mp3:
        #     continue
        bname = os.path.splitext(os.path.basename(fpath_mp3))[0]
        chunks = bname.split("-")

        call_direction = "N/A"
        if chunks[-1] == "in":
            call_direction = "IN"
            chunks.pop()
        elif chunks[-1] == "out":
            call_direction = "OUT"
            chunks.pop()

        g_dir = "N/A"
        if chunks[-1].startswith("GOUT"):
            g_dir = "GOUT"
        elif chunks[-1].startswith("GIM"):
            g_dir = "GIM"

        uid = "-".join(chunks)

        LOG.debug("Processing %d. (%s, %s) %s", n_mp3, g_dir, call_direction, fpath_mp3)

        try:
            zero_gaps, near_zero_gaps, sample_size = find_zero_gaps(fpath_mp3, min_dur_ms=1)
        except AudioFileError as e:
            LOG.warning("Skipping %s. %s", fpath_mp3, str(e))
            continue
        for gap in zero_gaps:
            sink.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(uid, g_dir, call_direction, "abs", gap[0], gap[1], gap[2], sample_size))
        for gap in near_zero_gaps:
            sink.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(uid, g_dir, call_direction, "near", gap[0], gap[1], gap[2], sample_size))

    sink.close()
    LOG.info(f"Stats are written to: {fpath_stats}")


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s", level=logging.DEBUG)
    logging.getLogger("ssa").setLevel(logging.ERROR)
    logging.getLogger("numba").setLevel(logging.ERROR)
    logging.getLogger("numba.core.ssa").setLevel(logging.ERROR)
    logging.getLogger("byteflow.dispatch").setLevel(logging.ERROR)
    run()
