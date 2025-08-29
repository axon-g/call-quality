
SCRIPT_DIR=/home/gpinter/GIT/axon/call-quality/src
PRJ_LIB_DIR=$(realpath "${SCRIPT_DIR}/../lib")

export PYTHONPATH=$PRJ_LIB_DIR

source "${SCRIPT_DIR}/.env"

python dev-01.py

