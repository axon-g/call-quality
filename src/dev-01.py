"""
Discover SHOPPERS audio -> MP3
"""
import datetime
import os
import logging
import numpy as np
import librosa
import joblib

from utils import find_subarray_ix

LOG = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BLD_DIR = os.path.join(SCRIPT_DIR, "..", "build")


MP3_ROOT = os.path.join("/usr/local/share/data/cv/audio/mp3")
# fix path
assert os.path.isdir(MP3_ROOT)


class Audio:
    def __init__(self, mp3_file, off: int = -1, size: int = -1):
        self.fpath = mp3_file
        self.off = off
        self.size = size



def iter_mp3():
    for root, _, fnames in os.walk(MP3_ROOT):
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

    # D = D.transpose()
    # diff = np.diff(D).shape
    #
    # # Diff with previous frame
    #
    #
    # import matplotlib.pyplot as plt
    # fig, ax = plt.subplots(nrows=2, sharex=True)
    # librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max),
    #                          y_axis='log', x_axis='time', ax=ax[0], sr=hz)
    # ax[0].set(title='Power spectrogram')
    # ax[0].label_outer()


def gen_feats(max_file_cnt: int, fft_pt: int, shift_pt: int) -> None:
    n_fft = 400
    shift = 200  # 25ms shift
    shift =  80  # 10ms shift
    n_fft = fft_pt
    shift = shift_pt

    n_mp3 = 0
    feats = []
    lens = []
    audios = []
    running_off = 0
    for fpath_mp3 in iter_mp3():
        LOG.debug("Processing %d. %s", n_mp3, fpath_mp3)
        n_mp3 += 1
        ffts, n_sample = analyze_one(fpath_mp3, n_fft=n_fft, shift=shift)
        # delta FFT is our feature
        feat = np.diff(ffts, axis=0)
        feats.append(feat)
        # lens.append(feat.shape[0])
        audios.append(Audio(mp3_file=fpath_mp3, size=feat.shape[0], off=running_off))
        running_off += feat.shape[0]

        if n_mp3 == max_file_cnt:
            break

    data = np.vstack(feats)
    # diffs = np.vstack([np.diff(mat, axis=0) for mat in feats])
    assert data.shape[0] == sum([audio.size for audio in audios])
    return data, audios


def train_gmm(X: np.ndarray):
    """
    :param X:  sample x feature
    :return:
    """
    LOG.info("Training GMM")
    from sklearn.mixture import GaussianMixture
    gmm = GaussianMixture(n_components=5,
                          covariance_type='tied',  # 'diag' is faster in high dim
                          reg_covar=1e-6,  # avoid singular covariances
                          random_state=42)
    t0 = datetime.datetime.now()
    gmm.fit(X)
    t_diff = datetime.datetime.now() - t0
    LOG.info("Trained {:,} samples in : {}".format(X.shape[0], t_diff))
    return gmm


def get_outliers(mdl, X) -> np.ndarray:
    """
    :param mdl:
    :param X:
    :return: indexes
    """
    neg_log_probs = -1.0*mdl.score_samples(X)  # shape (n_samples,)
    # np.histogram(log_probs, bins=100)
    n_bins = 100
    counts, bins = np.histogram(neg_log_probs, bins=n_bins)
    thresh = bins[n_bins//2 + 1]
    ixs = np.where(neg_log_probs > thresh)[0]
    return ixs
    # probs = np.exp(log_probs)         # actual probability densities



    # return neg_log_probs


def hist():
    import matplotlib.pyplot as plt
    plt.hist(log_probs, bins=30, color='skyblue', edgecolor='black')  # bins = number of bars
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Histogram Example')
    plt.show()

    plt.plot(np.exp(log_probs[:1000]), color='blue', linestyle='-', linewidth=2, label='sin(x)')

def dev():
    bname = os.path.splitext(os.path.basename(__file__))[0]
    ts = datetime.datetime.now().strftime("run-%Y%M%d_%H%M")
    dpath_out = os.path.join(BLD_DIR, bname, ts)
    os.makedirs(dpath_out, exist_ok=True)

    # params
    n_files = 2000
    fft_pt = 400
    shift_pt = 80
    # params: END

    X, audios = gen_feats(max_file_cnt=n_files, fft_pt=fft_pt, shift_pt=shift_pt)

    gmm = train_gmm(X)
    joblib.dump(gmm, os.path.join(dpath_out, "gmm.joblib"))

    outliers = get_outliers(gmm, X)
    off_cumsum = [a.off for a in audios]
    for tot_ix in outliers:
        audio_ix = find_subarray_ix(tot_ix, off_cumsum)
        pos_sample = tot_ix - audios[audio_ix-1].off
        pos_sec = ((pos_sample + 1) * 80) / 8000
        print(audios[audio_ix].fpath, pos_sec)


    # np.histogram(prob, bins=100)
    # indices = np.where(prob > threshold)[0]


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s %(message)s", level=logging.DEBUG)
    logging.getLogger("ssa").setLevel(logging.ERROR)
    logging.getLogger("numba").setLevel(logging.ERROR)
    logging.getLogger("numba.core.ssa").setLevel(logging.ERROR)
    logging.getLogger("byteflow.dispatch").setLevel(logging.ERROR)
    dev()
