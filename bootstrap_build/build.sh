#!/bin/bash
#  Copyright 2011 Digg, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

set -e

pushd ..

repo_top_dir=$(./bootstrap_build/find_top_of_repo.py)
package_output_dir=${repo_top_dir}/bootstrap-packages
repo_prefix_dir=digg/dev/hackbuilder
source_dir=${repo_top_dir}/bootstrap-source
build_dir=${repo_top_dir}/bootstrap-build/${repo_prefix_dir}
virtualenv_prefix_dir=third_party/virtualenv/virtualenv-1.6.4
virtualenv=${repo_top_dir}/bootstrap-source/${virtualenv_prefix_dir}/virtualenv.py
mach_agent_virtualenv_dir=${build_dir}/virtualenv
debian_packages_dir=${build_dir}/deb_packages
mach_agent_package_root=${debian_packages_dir}/digg-hack-builder
python=python2.5


function gen_binary () {
    do_build

    set -x

    echo 'Beginning package build'
    #make virtualenv relocatable
    ${python} ${virtualenv} --relocatable ${mach_agent_virtualenv_dir}

    mkdir ${debian_packages_dir}
    mkdir ${mach_agent_package_root}
    # create debian control file
    mkdir ${mach_agent_package_root}/DEBIAN
    cp bootstrap_build/debian/control ${mach_agent_package_root}/DEBIAN/control

    #create debian package hierarchy
    mkdir -p ${mach_agent_package_root}/usr/lib/digg-hack-builder
    cp -a ${mach_agent_virtualenv_dir} \
            ${mach_agent_package_root}/usr/lib/digg-hack-builder/virtualenv
    mkdir -p ${mach_agent_package_root}/usr/bin
    cp bootstrap_build/hack ${mach_agent_package_root}/usr/bin
    mkdir -p ${package_output_dir}

    #create debian binary package
    dpkg-deb -b ${mach_agent_package_root} ${package_output_dir}

    set +x
}


function do_build () {
    echo "Source directory: ${source_dir}"
    echo "Build directory: ${build_dir}"

    set -x

    mkdir -p ${build_dir}

    # copy dep source
    echo 'Beginning source tree creation'
    mkdir -p ${source_dir}/third_party/argparse
    cp -a ${repo_top_dir}/third_party/argparse/argparse-1.2.1/ \
            ${source_dir}/third_party/argparse/
    mkdir -p ${source_dir}/${repo_prefix_dir}
    cp -a ${repo_top_dir}/${repo_prefix_dir} \
            ${source_dir}/${repo_prefix_dir}/..
    # create setup.py
    ./bootstrap_build/gen_setup_py.py > ${source_dir}/setup.py

    # touch all __init__.py files
    touch ${source_dir}/digg/__init__.py
    touch ${source_dir}/digg/dev/__init__.py
    touch ${source_dir}/digg/dev/hackbuilder/__init__.py
    touch ${source_dir}/digg/dev/hackbuilder/cli/__init__.py
    touch ${source_dir}/digg/dev/hackbuilder/cli/commands/__init__.py
    touch ${source_dir}/digg/dev/hackbuilder/plugins/__init__.py

    echo 'Beginning build environment creation'
    mkdir -p ${source_dir}/third_party/virtualenv
    cp -a ${repo_top_dir}/${virtualenv_prefix_dir} \
            ${source_dir}/third_party/virtualenv/
    ${python} ${virtualenv} --no-site-packages --never-download --distribute \
            ${mach_agent_virtualenv_dir}

    #Install deps
    echo 'Beginning binary build'
    pushd ${source_dir}/third_party/argparse/argparse-1.2.1/
    ${mach_agent_virtualenv_dir}/bin/python setup.py install
    popd
    pushd ${source_dir}
    ${mach_agent_virtualenv_dir}/bin/python setup.py install
    popd

    set +x 
}

case $1 in
    binary)
        gen_binary
        ;;
    build)
        do_build
        ;;
    clean)
        rm -rf ../../../bootstrap-*
        ;;
    *)
        echo "Unknown target." 1>&2
        exit 1
        ;;
esac

popd
