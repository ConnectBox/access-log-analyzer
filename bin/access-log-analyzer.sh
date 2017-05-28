#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPT_PATH=`pwd`
popd > /dev/null

BASE_PATH="$(dirname "${SCRIPT_PATH}")"

export PYTHONPATH=$BASE_PATH/lib

python3 -m access_log_analyzer.main "$@"
