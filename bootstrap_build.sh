#!/bin/bash
cd bootstrap_build/; ./build.sh clean; ./build.sh build; cd ..
../../../bootstrap-build/digg/dev/hackbuilder/-hack/python_virtualenv/bin/hack clean
../../../bootstrap-build/digg/dev/hackbuilder/-hack/python_virtualenv/bin/hack build :hack
#../../../bootstrap-build/digg/dev/hackbuilder/-hack/python_virtualenv/bin/hack build :digg-hackbuilder
