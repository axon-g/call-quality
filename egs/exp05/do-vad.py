"""
Command line VAD tool wrapping PyAnnote.
Directory based: input/dirs have to be specified - not individual files.

'pyannote/segmentation-3.0' works only with 'pyannote.audio==3.0.0'  (3.0.1 is okay for non Apple Silicon)
"""
import datetime
import os
import sys
import wave
import logging
import click
from typing import Dict
from textgrid import TextGrid, IntervalTier
import soundfile

LOG = logging.getLogger(__file__)
HUGGING_FACE_TOKEN = "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"  # expires by 2024/03/31


class PyannoteVadWrapper:
    """
    Wraps Pyannote's Voice Activity Detector (VAD).
    The VAD model is fixed to 'pyannote/segmentation-3.0'
    """
    def __init__(self, vad_params: Dict = None, token: str = None):
        """
        @param vad_params: parameters when instantiating VAD pipeline (see VAD model page for details)
        @param token: Hugging Face access token
        """
        from pyannote.audio import Model
        from pyannote.audio.pipelines import VoiceActivityDetection

        self.model = Model.from_pretrained("pyannote/segmentation-3.0",
                                           use_auth_token=token if token else HUGGING_FACE_TOKEN)
        self.pipeline = VoiceActivityDetection(segmentation=self.model)
        self.params = vad_params if vad_params else {
          # remove speech regions shorter than that many seconds.
          "min_duration_on": 0.1,
          # fill non-speech regions shorter than that many seconds.
          "min_duration_off": 0.1
        }
        self.pipeline.instantiate(self.params)

    def segment(self, wav: str) -> TextGrid:
        """
        Performs VAD-based audio segmentation.
        @param wav: path to wav file to segment.
        @return: TextGrid object with "SPEECH" tier containing speech intervals
        """

        fsize = os.path.getsize(wav)
        if fsize <= 44:
            grid = TextGrid(name=wav, maxTime=0.0)
            tier = IntervalTier(name="SPEECH")
            grid.append(tier)
            return grid

        from pyannote.core.annotation import Annotation
        segmented: Annotation = self.pipeline(wav)

        with wave.open(wav) as fh:
            tot_dur = fh.getnframes() / fh.getframerate()
        grid = TextGrid(name=segmented.uri, maxTime=tot_dur)
        tier = IntervalTier(name="SPEECH")
        grid.append(tier)
        end_max = 0.0
        for seg, _ in segmented.itertracks():
            tier.add(seg.start, seg.end, "SPEECH")
            end_max = max(end_max, seg.end)
        if end_max < tot_dur:
            tier.add(end_max, tot_dur, "")

        return grid


@click.command()
@click.argument('audio-dir', type=click.Path(dir_okay=True, file_okay=False, exists=True))
@click.argument('label-dir', type=click.Path(dir_okay=True, file_okay=False), nargs=-1)
@click.option("--overwrite", default=True, type=click.BOOL, help="Flag to overwrite VAD labels (True)")
@click.option("--ext", default=".grid", type=click.STRING, help="Extension for VAD labels (.grid)")
def process_dir(audio_dir: str, label_dir: str = "ad!", ext: str = ".grid", overwrite: bool = True) -> None:
    """
    Searches for .wav files in AUDIO_DIR and performs Voice Activity Detection (VAD).
    Writes VAD labels to OUT_DIR, if not provided it writes labels to the audio directory, next to audio files.
    """
    # prefix extensions with '.' if missing
    ext = f".{ext}" if ext[0] != "." else ext

    label_dir = audio_dir if len(label_dir) == 0 else label_dir[0]

    vad = PyannoteVadWrapper()

    t0 = datetime.datetime.now()
    log_every_sec = 10
    file_cnt = 0
    for root, _, fnames in os.walk(audio_dir):
        for fname in [f for f in fnames if f.lower().endswith(".wav")]:
            file_cnt += 1
            fpath_wav = os.path.join(root, fname)
            relpath = os.path.relpath(fpath_wav, audio_dir)

            relpath_out = "{}{}".format(os.path.splitext(relpath)[0], ext)
            fpath_label = os.path.join(label_dir, relpath_out)

            if not overwrite and os.path.isfile(fpath_label):
                LOG.debug(f"Skipping {fpath_label}")
                continue

            try:
                grid: TextGrid = vad.segment(fpath_wav)
            except soundfile.LibsndfileError:
                LOG.error(f"Skipping wrong audio format: {fpath_label}")
                continue

            nseg = len([1 for ival in grid.tiers[0] if ival.mark.strip() != ""])
            if nseg == 0:  # empty, not recognized
                LOG.info(f"No speech in: {fpath_wav}")
                fpath_label = f"{fpath_label}.empty"
                continue
            else:
                t = datetime.datetime.now()
                if (t - t0).seconds > log_every_sec:
                    LOG.info(f"Writing: {file_cnt:6d} {fpath_label} (seg={nseg})")
                    t0 = t
            os.makedirs(os.path.dirname(fpath_label), exist_ok=True)
            grid.write(fpath_label)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        process_dir.main(['--help'])
    else:
        logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s",
                            level=logging.INFO)
        process_dir()
