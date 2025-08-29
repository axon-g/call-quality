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


LOG = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BLD_DIR = os.path.join(SCRIPT_DIR, "..", "build")

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
    y, hz = librosa.load(audio_file, sr=None, mono=False)
    if y.shape[0] == 0:
        return []

    values, counts = np.unique(y, return_counts=True)
    index = np.argmax(counts)
    mode = values[index]

    # threshold: min number of samples in span
    thresh = int(np.ceil((min_dur_ms/1000) * hz))

    def find_spans(ixs: np.ndarray):
        if ixs.shape[0] == 0:
            return []
        spans = []
        span_len = 0
        span_start = ixs[0]

        for iix, ix in enumerate(ixs):
            if ixs[iix] == ixs[iix-1] + 1:
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

    filtered_abs_zero = [g  for g in gaps_abs_zero if g[1] > thresh]
    filtered_near_zero = [g  for g in gaps_almost_zero if g[1] > thresh]
    return filtered_near_zero



def run():
    bname = os.path.splitext(os.path.basename(__file__))[0]
    ts = datetime.datetime.now().strftime("run-%Y%M%d_%H%M")
    dpath_out = os.path.join(BLD_DIR, bname, ts)
    os.makedirs(dpath_out, exist_ok=True)

    fpath_stats = os.path.join(dpath_out, "sil-gap-stats.csv")
    sink = open(fpath_stats, "w", encoding="utf-8")
    sink.write("{}\t{}\t{}\t{}\n".format("uid", "call.dir", "span.off", "span.size"))

    n_mp3 = 0
    for fpath_mp3 in iter_mp3():
        LOG.debug("Processing %d. %s", n_mp3, fpath_mp3)
        # if "20250828-100407-99000000230000001170-GOUT00000023902001-out" not in fpath_mp3:
        #     continue

        bname = os.path.splitext(os.path.basename(fpath_mp3))[0]
        call_direction = "n/a"
        if bname.endswith("-out"):
            call_direction = "out"
            uid = bname.replace("-out", "")
        elif bname.endswith("-in"):
            call_direction = "in"
            uid = bname.replace("-in", "")
        else:
            uid = bname
        gaps = find_zero_gaps(fpath_mp3, min_dur_ms=20)
        for gap in gaps:
            sink.write("{}\t{}\t{}\t{}\n".format(uid, call_direction, gap[0], gap[1]))
        n_mp3 += 1

    sink.close()
    LOG.info(f"Stats are written to: {fpath_stats}")


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s", level=logging.DEBUG)
    logging.getLogger("ssa").setLevel(logging.ERROR)
    logging.getLogger("numba").setLevel(logging.ERROR)
    logging.getLogger("numba.core.ssa").setLevel(logging.ERROR)
    logging.getLogger("byteflow.dispatch").setLevel(logging.ERROR)
    run()
