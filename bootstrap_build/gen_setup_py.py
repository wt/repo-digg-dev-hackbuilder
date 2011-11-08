#!/usr/bin/env python2.5
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


def build_target_python_bin(target_name, entry_point, deps):
    packages = [
            'digg',
            'digg.dev',
            'digg.dev.hackbuilder',
            'digg.dev.hackbuilder.cli',
            'digg.dev.hackbuilder.cli.commands',
            'digg.dev.hackbuilder.plugins',
            ]

    setup_script_text = (
            '\n'
            'setuptools.setup(\n'
            "    name='" + target_name + "',\n"
            "    packages=['" + "','".join(packages) + "'],\n"
            '    entry_points={\n'
            "        'console_scripts': [\n"
            "            '" + target_name + ' = ' + entry_point + "',\n"
            '        ],\n'
            '    },\n'
            '    zip_safe=False,\n'
            ')'
            )

    build_targets[target_name] = {
            'type': 'python_bin',
            'entry_point': entry_point,
            'packages': packages,
            'deps': deps,
            'setup_script_text': setup_script_text
            }

build_targets = {}

build_globals = {}
build_locals = {
        'debian_pkg': lambda *args, **kwargs: None,
        'python_bin': build_target_python_bin,
        'python_test': build_target_python_bin,
        'python_lib': lambda *args, **kwargs: None,
        }
execfile('HACK_BUILD', build_globals, build_locals)

print 'import setuptools\n'
for target, attrs in build_targets.iteritems():
    print attrs['setup_script_text']
