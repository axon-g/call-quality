SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# creates opus decoded audio

set -e

WAV_DIR=$(realpath ${SCRIPT_DIR}/../sample-audio)
OUT_DIR=$(realpath ${SCRIPT_DIR}/../build/encoded)

mkdir -p $OUT_DIR

INPUT="${WAV_DIR}/g_23_sample.wav"

OUT=${OUT_DIR}/g_23_sample.ulaw.wav
echo "Writing file: $OUT"
sox $INPUT -e mu-law -t wav - | sox - -e signed-integer -t wav -r 8000 -b 16 -c 1 $OUT

for frame in 10 20 40 60 ; do
for bitrate in 32 48 64  ; do
for loss_rate in 10 20 30 40 50 60 70 80 90; do
    OUT="${OUT_DIR}/g_23_sample.bitrate${bitrate}.frame${frame}.eloss${loss_rate}.opus"
    echo "Out file: $OUT"
#    opusenc --bitrate ${bitrate} --framesize ${frame} --vbr --speech --expect-loss ${loss_rate} $INPUT $OUT
    opusenc --bitrate ${bitrate} --framesize ${frame} --hard-cbr  --speech --expect-loss ${loss_rate} $INPUT $OUT
done
done
done
