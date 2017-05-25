#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPT_PATH=`pwd`
popd > /dev/null

BASE_PATH="$(dirname "${SCRIPT_PATH}")"

python3 -m unittest access_log_analyzer.tests.test_ingestor
python3 -m unittest access_log_analyzer.tests.test_reporting
