#!/bin/bash
cd bootstrap_build/; ./build.sh clean; ./build.sh build; cd ..
../../../bootstrap-build/digg/dev/hackbuilder/-hack/python_virtualenv/bin/hack clean
../../../bootstrap-build/digg/dev/hackbuilder/-hack/python_virtualenv/bin/hack build :hack
echo '************************************************************************************************'
echo "Here's an alias to make using the bootstrap version of hack easier:"
echo "alias hack=${PWD}/../../../bootstrap-build/digg/dev/hackbuilder/-hack/python_virtualenv/bin/hack"
echo '************************************************************************************************'
