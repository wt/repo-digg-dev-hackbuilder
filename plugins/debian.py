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

import logging
import os.path
import subprocess

import digg.dev.hackbuilder.target
import digg.dev.hackbuilder.plugin_utils
from digg.dev.hackbuilder.plugins import build_file_targets
from digg.dev.hackbuilder.plugin_utils \
        import normal_dep_targets_from_dep_strings
from digg.dev.hackbuilder.plugin_utils import BinaryBuilder


class DebianPackageBuilder(digg.dev.hackbuilder.plugin_utils.PackageBuilder):
    def __init__(self, target):
        digg.dev.hackbuilder.plugin_utils.PackageBuilder.__init__(self, target)

        self.full_package_hierarchy_dir = os.path.join(
                self.target.target_build_dir, 'dpkg_hierarchy')

    def do_pre_build_package_binary_install(self, builders):
        logging.info('Copying built binaries to package hierarchy for %s',
                self.target.target_id)

        for dep_id in self.target.dep_ids:
            builder = builders[dep_id]
            if isinstance(builder, BinaryBuilder):
                builder.do_pre_build_package_binary_install(builders, self)


    def do_build_package_work(self):
        self._create_debian_control_file()
        self._create_debian_binary_package()

    def _create_debian_control_file(self):
        logging.info('Creating Debian control file for %s', self.target.target_id)
        logging.info('Getting Debian architecture')
        deb_arch_proc = subprocess.Popen(
                ['dpkg-architecture', '-qDEB_BUILD_ARCH'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = deb_arch_proc.communicate()
        retcode = deb_arch_proc.returncode
        if retcode != 0:
            logging.info(
                    'Finding Debian architecture failed with exit code = %s.',
                    retcode)
            logging.info('Finding Debian architecture stdout:\n%s',
                    stdoutdata)
            logging.info('Finding Debian architecture stderr:\n%s',
                    stderrdata)
            raise digg.dev.hackbuilder.errors.Error(
                    'dpkg-architecture call failed with exitcode %s', retcode)
        deb_arch = stdoutdata.strip()
        logging.info('Debian architecture: %s', deb_arch)

        control_file_text = (
                'Package: %s\n'
                'Version: %s\n'
                'Architecture: %s\n'
                'Maintainer: Digg Ops <ops@digg.com>\n'
                'Depends: %s\n'
                'Description: %s\n'
                '%s\n' %
                (self.target.target_id.name,
                 self.target.dpkg_version,
                 deb_arch,
                 ', '.join(self.target.dpkg_deps),
                 'stuff',
                 ' More stuff.'
                 ))
        logging.debug('Debian control file text:\n%s', control_file_text)

        logging.info('Writing Debian control file for %s',
                self.target.target_id)
        full_dir = os.path.join(self.full_package_hierarchy_dir, 'DEBIAN')
        full_path = os.path.join(full_dir, 'control')
        logging.debug('Debian control file absolute path: %s', full_path)
        os.makedirs(full_dir)
        with open(full_path, 'w') as deb_control_file:
            deb_control_file.write(control_file_text)

    def _create_debian_binary_package(self):
        logging.info('Creating Debian binary package for %s', self.target.target_id)
        dpkg_deb_proc = subprocess.Popen(
                    ('dpkg-deb', '-b', self.full_package_hierarchy_dir,
                     self.target.package_root,
                     ),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = dpkg_deb_proc.communicate()
        retcode = dpkg_deb_proc.returncode
        if retcode != 0:
            logging.info('Debian binary package creation failed.')
            logging.info('Making virtualenv relocatable failed with exit code = %s',
                    retcode)
            logging.info('Making virtualenv relocatable stdout:\n%s',
                    stdoutdata)
            logging.info('Making virtualenv relocatable stderr:\n%s',
                    stderrdata)
            raise digg.dev.hackbuilder.errors.Error(
                    'dpkg-deb call failed with exitcode %s', retcode)

        package_file_path = stdoutdata.split()[5][1:-2]
        logging.info('Package build at: %s', package_file_path)


class DebianPackageBuildTarget(
        digg.dev.hackbuilder.target.PackageBuildTarget):
    builder_class = DebianPackageBuilder

    def __init__(self, normalizer, target_id, dep_ids=None, dpkg_version=None,
            extra_dpkg_deps=None):
        digg.dev.hackbuilder.target.PackageBuildTarget.__init__(self,
                normalizer, target_id, dep_ids)

        if dpkg_version is None:
            self.dpkg_version = '0.0.0.0.1'
        else:
            self.dpkg_version = dpkg_version

        self.dpkg_deps = set([
                'libc6 (>= 2.7-1)',
                'python2.6'
                ])
        if extra_dpkg_deps is not None:
            self.dpkg_deps.update(extra_dpkg_deps)


def build_file_debian_pkg(repo_path, normalizer):
    def debian_pkg(name, deps=(), version=None, extra_dpkg_deps=None):
        logging.debug('Build file target, Debian package: %s', name)
        target_id = digg.dev.hackbuilder.target.TargetID(repo_path, name)
        dep_target_ids = normal_dep_targets_from_dep_strings(repo_path,
                normalizer, deps)
        debian_pkg_target = DebianPackageBuildTarget(normalizer, target_id,
                dep_ids=dep_target_ids, dpkg_version=version,
                extra_dpkg_deps=extra_dpkg_deps)
        build_file_targets.put(debian_pkg_target)

    return debian_pkg


def build_file_rules_generator(repo_path, normalizer):
    build_file_rules = {
            'debian_pkg': build_file_debian_pkg(repo_path, normalizer),
            }
    return build_file_rules
