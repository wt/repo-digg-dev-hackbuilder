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

from __future__ import with_statement

import errno
import logging
import os.path
import shutil
import subprocess

import digg.dev.hackbuilder.target
import digg.dev.hackbuilder.plugin_utils
import digg.dev.hackbuilder.util
from digg.dev.hackbuilder.plugins import build_file_targets
from digg.dev.hackbuilder.plugin_utils \
        import normal_dep_targets_from_dep_strings

DEFAULT_PYTHON = 'python2.6'
DEFAULT_VIRTUALENV_VERSION = '1.6.4'
VIRTUALENV_REPO_PATH = os.path.join(
        'third_party', 'virtualenv',
        'virtualenv-' + DEFAULT_VIRTUALENV_VERSION)


def add_argparser_arguments(parser):
    parser.add_argument('--python_install_method', default='install',
            choices=['install', 'develop'], nargs='?',
            help='Choose method for python package installation. The '
                 '"install" method copies over files. The "develop" method '
                 'installs a package in develop mode so mode so that source '
                 'changes are picked up without reinstalling the package. '
                 'Working packages can only be built with the "install" '
                 'method. (Default: install)')


class PythonBinaryBuilder(digg.dev.hackbuilder.plugin_utils.BinaryBuilder):
    def __init__(self, target):
        digg.dev.hackbuilder.plugin_utils.BinaryBuilder.__init__(self,
                target)

        self.virtualenv_tool_path = os.path.join(
                self.normalizer.repo_root_path,
                VIRTUALENV_REPO_PATH, 'virtualenv.py')

    def do_pre_create_source_tree_work(self, builders):
        logging.info('Creating %s-setup.py for %s',
                self.target.target_id.name, self.target.target_id)

        packages = set()
        current_package = ''
        for path_part in (
                self.target.target_id.path[1:].split(os.path.sep)[:-1]):
            current_package = '.'.join([current_package, path_part])
            packages.add(current_package[1:])

        for dep_id in self.target.dep_ids:
            builder = builders[dep_id]
            if isinstance(builder, PythonLibraryBuilder):
                packages.update(builder.get_transitive_python_packages(
                    builders))

        packages_string = ''
        if packages:
            packages_string = "'%s'" % "','".join(packages)

        setup_py_text = (
                'import setuptools\n'
                '\n'
                'setuptools.setup(\n'
                "    name='%s',\n"
                '    packages=[%s],\n'
                '    entry_points={\n'
                "        'console_scripts': [\n"
                "            '%s = %s',\n"
                '        ],\n'
                '    },\n'
                ')' %
                (self.target.target_id.name,
                 packages_string,
                 self.target.target_id.name,
                 self.target.entry_point))
        logging.debug('Setup script contents:\n%s' % setup_py_text)

        logging.debug('Absolute setup script path: %s',
                self.target.setup_py_path)
        with open(self.target.setup_py_path, 'w') as f:
            f.write(setup_py_text)

    def do_create_build_environment_work(self):
        logging.info('Creating virtualenv for %s', self.target.target_id)
        logging.debug('Absolute path for virtualenv: %s',
                self.target.virtualenv_root)
        logging.debug('Absolute path for virtualenv tool: %s',
                self.virtualenv_tool_path)

        virtualenv_proc = subprocess.Popen(
                    (DEFAULT_PYTHON, self.virtualenv_tool_path,
                     '--no-site-packages', '--never-download', '--distribute',
                     self.target.virtualenv_root
                     ),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = virtualenv_proc.communicate()
        retcode = virtualenv_proc.returncode
        if retcode != 0:
            logging.info('Virtualenv creation failed with exit code = %s',
                    retcode)
            logging.info('Virtualenv creation stdout:\n%s', stdoutdata)
            logging.info('Virtualenv creation stderr:\n%s', stderrdata)
            raise digg.dev.hackbuilder.errors.Error(
                    'Virtualenv creation failed.')

    def do_pre_build_binary_library_install(self, builders):
        logging.info('Installing libs for binary build for %s',
                self.target.target_id)

        for dep_id in self.target.dep_ids:
            builder = builders[dep_id]
            if isinstance(builder, PythonLibraryBuilder):
                builder.do_pre_build_binary_library_install(builders, self)

    def do_build_binary_work(self):
        logging.info('Installing libs into virtualenv for %s',
                self.target.target_id)

        python_bin_path = os.path.join(self.target.virtualenv_root,
                'bin', 'python')
        installer_proc = subprocess.Popen(
                (python_bin_path, self.target.setup_py_path,
                    ARGS.python_install_method),
                cwd=self.target.source_root,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = installer_proc.communicate()
        retcode = installer_proc.returncode
        if retcode != 0:
            logging.info('Install failed with exit code = %s',
                    retcode)
            logging.info('Install stdout:\n%s', stdoutdata)
            logging.info('Install stderr:\n%s', stderrdata)
            raise digg.dev.hackbuilder.errors.Error(
                    'Install failed.')

    def do_pre_build_package_binary_install(self, builders, package_builder):
        logging.info('Copying binary for %s to package %s',
                self.target.target_id, package_builder.target.target_id)

        full_virtualenv_dest_path = os.path.join(
                package_builder.full_package_hierarchy_dir, 'usr', 'lib',
                package_builder.target.target_id.name, 
                '-'.join((self.target.target_id.name, 'virtualenv')))
        shutil.copytree(self.target.virtualenv_root, full_virtualenv_dest_path,
                True)

        logging.info('Creating wrapper script for %s for package %s',
                self.target.target_id, package_builder.target.target_id)
        full_entry_point_wrapper_dir = os.path.join(
                package_builder.full_package_hierarchy_dir, 'usr', 'bin')
        os.mkdir(full_entry_point_wrapper_dir)
        full_entry_point_wrapper_path = os.path.join(
                full_entry_point_wrapper_dir, self.target.target_id.name)

        entry_point_exec_target = os.path.join('../lib/',
                package_builder.target.target_id.name,
                '-'.join((self.target.target_id.name, 'virtualenv')), 'bin',
                self.target.target_id.name)

        with open(full_entry_point_wrapper_path, 'w') as f:
            f.write('#!/bin/bash -e\n')
            f.write('DIR="$( cd -P "$( dirname "$0" )" && pwd )"\n')
            f.write('exec ${DIR}/%s "$@"' % (entry_point_exec_target,))
        os.chmod(full_entry_point_wrapper_path, 0755)

    def do_build_package_work(self):
        logging.info('Making built virtualenv relocatable for %s',
                self.target.target_id)
        virtualenv_proc = subprocess.Popen(
                    (DEFAULT_PYTHON, self.virtualenv_tool_path,
                     '--relocatable', self.target.virtualenv_root
                     ),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = virtualenv_proc.communicate()
        retcode = virtualenv_proc.returncode
        if retcode != 0:
            logging.info('Making virtualenv relocatable failed with exit code = %s',
                    e.returncode)
            logging.info('Making virtualenv relocatable stdout:\n%s',
                    stdoutdata)
            logging.info('Making virtualenv relocatable stderr:\n%s',
                    stderrdata)
            raise digg.dev.hackbuilder.errors.Error(
                    'Making virtualenv relocatable failed.')


class PythonBinaryBuildTarget(digg.dev.hackbuilder.target.BinaryBuildTarget):
    builder_class = PythonBinaryBuilder

    def __init__(self, normalizer, target_id, dep_ids, entry_point=None):
        digg.dev.hackbuilder.target.BinaryBuildTarget.__init__(self,
                normalizer, target_id, dep_ids)
        self.entry_point = entry_point
        self.virtualenv_root = os.path.join(self.target_build_dir,
                'python_virtualenv')
        self.bin_path = os.path.join(self.virtualenv_root, 'bin',
                self.target_id.name)
        self.setup_py_path = os.path.join(
                self.target_source_dir,
                'setup-%s.py' % self.target_id.name)


class PythonTestBuilder(PythonBinaryBuilder):
    pass


class PythonTestBuildTarget(PythonBinaryBuildTarget):
    builder_class = PythonTestBuilder


class PythonLibraryBuilder(digg.dev.hackbuilder.plugin_utils.LibraryBuilder):
    def get_transitive_python_packages(self, builders):
        packages = set(self.target.packages)
        for dep_id in self.target.dep_ids:
            builder = builders[dep_id]
            if isinstance(builder, PythonLibraryBuilder):
                packages.update(builder.get_transitive_python_packages(
                    builders))

        return packages

    def do_pre_build_binary_library_install(self, builders, binary_builder):
        for dep_id in self.target.dep_ids:
            builder = builders[dep_id]
            if isinstance(builder, PythonLibraryBuilder):
                builder.do_pre_build_binary_library_install(builders,
                        binary_builder)

    def do_create_source_tree_work(self):
        digg.dev.hackbuilder.plugin_utils.LibraryBuilder.do_create_source_tree_work(
                self)
        self._create_init_py_files()

    def _create_init_py_files(self):
        logging.info('Creating missing __init__.py files.')

        # for directories above this package
        split_path = self.target.target_id.path[1:].split(os.path.sep)
        last_path = ''
        for path in split_path:
            repo_path = os.path.join(last_path, path)
            init_py_repo_path = os.path.join(repo_path, '__init__.py')
            full_path = os.path.join(self.target.source_root,
                    init_py_repo_path)
            if not os.path.exists(full_path):
                logging.info('Creating empty file: %s', init_py_repo_path)
                logging.debug('Creating empty file: %s', full_path)
                with open(full_path, 'w') as f:
                    # just need to create the file
                    pass
            last_path = os.path.join(last_path, path)

        # for packages in this package
        for package in self.target.packages:
            repo_path_parts = package.split('.')
            repo_path_parts.append('__init__.py')
            init_py_repo_path  = os.path.join(*repo_path_parts)
            full_path = os.path.join(self.target.source_root,
                    *repo_path_parts)
            if not os.path.exists(full_path):
                logging.info('Creating empty file: %s', init_py_repo_path)
                logging.debug('Creating empty file: %s', full_path)
                with open(full_path, 'w') as f:
                    # just need to create the file
                    pass


class PythonLibraryBuildTarget(digg.dev.hackbuilder.target.LibraryBuildTarget):
    builder_class = PythonLibraryBuilder

    def __init__(self, normalizer, target_id, dep_ids, files, packages=None):
        digg.dev.hackbuilder.target.BuildTarget.__init__(self, normalizer,
                target_id, dep_ids=dep_ids)
        self.files = files
        self.packages = packages


class PythonThirdPartyLibraryBuilder(PythonLibraryBuilder):
    def get_transitive_python_packages(self, builders):
        return set()

    def do_pre_build_binary_library_install(self, builders, binary_builder):
        for dep_id in self.target.dep_ids:
            builder = builders[dep_id]
            if isinstance(builder, PythonLibraryBuilder):
                builder.do_pre_build_binary_library_install(builders,
                        binary_builder)

        logging.info('Installing %s in %s binary build directory' %
                (self.target.target_id, binary_builder.target.target_id))
        python_bin_path = os.path.join(binary_builder.target.virtualenv_root,
                'bin', 'python')
        full_target_path = os.path.join(self.target.target_source_dir,
                self.target.lib_dir)
        installer_proc = subprocess.Popen(
                (python_bin_path, 'setup.py', 'install'),
                cwd=full_target_path,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = installer_proc.communicate()
        retcode = installer_proc.returncode
        if retcode != 0:
            logging.info('Library install failed with exit code = %s',
                    retcode)
            logging.info('Library install stdout:\n%s', stdoutdata)
            logging.info('Library install stderr:\n%s', stderrdata)
            raise digg.dev.hackbuilder.errors.Error(
                    'Library install failed.')

    def do_create_source_tree_work(self):
        logging.info('Copying %s into source tree using source lib_dir (%s)',
                self.target.target_id, self.target.normal_lib_dir)
        full_src_path = os.path.join(self.target.target_working_copy_dir,
                self.target.lib_dir)
        full_target_path = os.path.join(self.target.target_source_dir,
                self.target.lib_dir)
        digg.dev.hackbuilder.util.mirror_filesystem_hierarchy(
                full_src_path,
                full_target_path)


class PythonThirdPartyLibraryBuildTarget(
        digg.dev.hackbuilder.target.LibraryBuildTarget):
    builder_class = PythonThirdPartyLibraryBuilder

    def __init__(self, normalizer, target_id, dep_ids, lib_dir=None):
        digg.dev.hackbuilder.target.BuildTarget.__init__(self, normalizer,
                target_id, dep_ids)
        self.lib_dir = lib_dir
        self.normal_lib_dir = self.normalizer.normalize_path_in_build_file(
                lib_dir, self.target_id.path)


def build_file_python_bin(repo_path, normalizer):
    def python_bin(name, deps=(), entry_point=None):
        logging.debug('Build file target, Python bin: %s', name)
        target_id = digg.dev.hackbuilder.target.TargetID(repo_path, name)
        dep_target_ids = normal_dep_targets_from_dep_strings(repo_path,
                normalizer, deps)
        python_bin_target = PythonBinaryBuildTarget(normalizer, target_id,
                dep_ids=dep_target_ids, entry_point=entry_point)
        build_file_targets.put(python_bin_target)

    return python_bin


def build_file_python_test(repo_path, normalizer):
    def python_test(name, deps=(), entry_point=None):
        logging.debug('Build file target, Python test: %s', name)
        target_id = digg.dev.hackbuilder.target.TargetID(repo_path, name)
        dep_target_ids = normal_dep_targets_from_dep_strings(repo_path,
                normalizer, deps)
        python_test_target = PythonTestBuildTarget(normalizer, target_id,
                dep_ids=dep_target_ids, entry_point=entry_point)
        build_file_targets.put(python_test_target)

    return python_test


def build_file_python_lib(repo_path, normalizer):
    def python_lib(name, deps=(), files=None, packages=None):
        logging.debug('Build file target, Python lib: %s', name)
        target_id = digg.dev.hackbuilder.target.TargetID(repo_path, name)
        dep_target_ids = normal_dep_targets_from_dep_strings(repo_path,
                normalizer, deps)
        python_lib_target = PythonLibraryBuildTarget(normalizer, target_id,
                dep_ids=dep_target_ids, files=files, packages=packages)
        build_file_targets.put(python_lib_target)

    return python_lib


def build_file_python_third_party_lib(repo_path, normalizer):
    def python_third_party_lib(name, deps=(), lib_dir=None):
        logging.debug('Build file target, Python 3rd party lib: %s', name)
        target_id = digg.dev.hackbuilder.target.TargetID(repo_path, name)
        dep_target_ids = normal_dep_targets_from_dep_strings(repo_path,
                normalizer, deps)
        python_third_party_lib_target = PythonThirdPartyLibraryBuildTarget(
                normalizer, target_id, dep_ids=dep_target_ids, lib_dir=lib_dir)
        build_file_targets.put(python_third_party_lib_target)

    return python_third_party_lib


def build_file_rules_generator(repo_path, normalizer):
    build_file_rules = {
            'python_bin': build_file_python_bin(repo_path, normalizer),
            'python_test': build_file_python_test(repo_path, normalizer),
            'python_lib': build_file_python_lib(repo_path, normalizer),
            'python_third_party_lib':
            build_file_python_third_party_lib(repo_path, normalizer),
            }
    return build_file_rules
