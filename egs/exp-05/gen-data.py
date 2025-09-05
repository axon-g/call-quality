"""
This script does something.
"""
import logging
import os
from typing import List, Dict, Tuple

import polars
import textgrid

LOG = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

"""
Expected structure
build/
├── exp-02
│   └── run-20250902_1727
│       └─  sil-gap-stats.parquet    # SIL stats
└── exp-05
    └── label-vad                    # VAD labels
        ├── 20250827
        ├── ...
        └── 20250901
"""


PRJ_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
BLD_DIR_EXP2 = os.path.join(PRJ_ROOT, 'build', 'exp-02')
BLD_DIR_EXP5 = os.path.join(PRJ_ROOT, 'build', 'exp-05')
VAD_DIR = os.path.join(BLD_DIR_EXP5, "label-vad")


if not os.path.isdir(BLD_DIR_EXP2):
    raise ValueError('Cannot find dir for SIL stats: %s' % BLD_DIR_EXP2)

if not os.path.isdir(BLD_DIR_EXP5):
    raise ValueError('Cannot find dir for VAD stats: %s' % BLD_DIR_EXP5)

if not os.path.isdir(VAD_DIR):
    raise ValueError('Cannot find dir for VAD stats: %s' % VAD_DIR)


def get_sil_stat_df(parquet_file: str = "sil-gap-stats.parquet") -> polars.dataframe.frame.DataFrame:
    """
    :return:
    """
    target_files = []
    for root, _, fnames in os.walk(BLD_DIR_EXP2):
        for fname in [f for f in fnames if f == parquet_file]:
            rel_path = os.path.relpath(os.path.join(root, fname), BLD_DIR_EXP2)
            target_files.append(rel_path)

    if len(target_files) == 0:
        raise ValueError(f"Cannot find data {parquet_file} in dir: {BLD_DIR_EXP2}")

    fpath_parquet = os.path.join(BLD_DIR_EXP2, sorted(target_files)[-1])

    df = polars.read_parquet(fpath_parquet)
    return df


def get_vad_labels() -> Dict[str, List[Tuple[float, float]]]:
    """
    :return: dict with key: UID-{in,out}, value list of start/end of speech intervals
    """
    data = {}
    for root, _, fnames in os.walk(VAD_DIR):
        for fname in [f for f in fnames if (f.endswith("-in.grid") or f.endswith("-out.grid"))]:
            fpath_grid = os.path.join(root, fname)

            bname = os.path.splitext(fname)[0]
            *uid_chunks, direction = bname.split("-")
            uid = "-".join(uid_chunks)
            key = (uid, direction)

            grid = textgrid.TextGrid.fromFile(fpath_grid, uid)
            data[key] = [(int(ival.minTime*8000), int(ival.maxTime*8000), 1) for ival in grid.tiers[0] if ival.mark == "SPEECH"]
    return data


def dev() -> None:
    # get SIL stats
    vad = get_vad_labels()
    df = get_sil_stat_df()

    for (uid, direction), speech_ivals in vad.items():
        tbl = df.filter(
            (polars.col("uid") == uid) & (polars.col("direction") == direction.upper()) & (polars.col("zero") == "abs")
        ).sort(polars.col("span.off"))

        if tbl.shape[0] == 0:
            continue

        SIL = [(a, a+b, 0) for a, b in zip(tbl["span.off"].to_list(), tbl["span.size"].to_list())]

        sorted(SIL + speech_ivals)
        #  (200117, 200144, 0),
        #  (200171, 200210, 0),
        #  (200182, 202207, 1),
        #  (200211, 200234, 0),
        #  (200237, 200246, 0),



if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s", level=logging.DEBUG)
    dev()
