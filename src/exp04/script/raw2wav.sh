SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

set -e

RAW_DIR=$(realpath ${SCRIPT_DIR}/../build/decoded-raw)
WAV_DIR=$(realpath ${SCRIPT_DIR}/../build/decoded-wav)
mkdir -p $WAV_DIR


for raw in `find $RAW_DIR -name "*raw" -type f` ; do
  bname=$(basename $raw)
  fpath_wav="${WAV_DIR}/${bname%.raw}.wav"
  echo $fpath_wav

   if [[ "$file" == *ulaw* ]]; then
      sox -r 16000 -c 1 -e signed-integer -b 16 $raw $fpath_wav
    else
      sox -r 16000 -c 1 -e signed-integer -b 16 $raw $fpath_wav
    fi
#  echo $raw
#  sox -t raw -r 16000 -e signed-integer -c 1
done