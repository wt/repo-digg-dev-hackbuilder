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
import re
import sys

import digg.dev.hackbuilder.common
import digg.dev.hackbuilder.errors


class Normalizer(object):
    """Target normalizer.

    This object is used to transform repository paths into normaized versions
    whose paths are absolute within the repository.

    Attributes:
        repo_root_path: The absolute filesystem path to the repository root.
    """

    def __init__(self, repo_root_path):
        """Normalizer initializer.

        Args:
            repo_root_path: The path to the root of the repository
        """
        self.repo_root_path = os.path.abspath(repo_root_path)

    def normalize_target_id(self, target_id):
        """Normalize a target id.

        Args:
            target_id: a TargetID object

        Returns: a normalized target_id
        """
        if target_id.is_normalized():
            return target_id

        if target_id.is_relative():
            path = self.normalize_path(target_id.path)
        else:
            path = target_id.path

        if target_id.has_name():
            name = target_id.name
        else:
            name = ''

        return TargetID(path, target_id.name)

    def normalize_target_id_with_name(self, target_id):
        """Normalize a target id that has a name.

        Args:
            target_id: a TargetID object with a name

        Raises:
            digg.dev.hackbuilder.errors.Error: if the target_id does not have
                a name
        """
        if not target_id.has_name():
            raise digg.dev.hackbuilder.errors.Error(
                    'The target id does not have a name.'
                    % target_id)

        return self.normalize_target_id(target_id)

    def normalize_path(self, path):
        """Get the relative path from the repository root to a path.

        Args:
            path: The path string to which to find the relative path

        Returns: The relative path string that leads from the repository root
            to the path.
        """
        abs_path = os.path.abspath(path)
        common_prefix = os.path.commonprefix((self.repo_root_path, abs_path))
        if not common_prefix == self.repo_root_path:
            raise digg.dev.hackbuilder.errors.Error(
                    'The target id path is not within a code repository.')

        # TODO(wt): for python 2.6+, the following line can be replaced with:
        # return '/' + os.path.relpath(abs_path, self.repo_root_path)
        return self._relpath(abs_path, self.repo_root_path)

    def _relpath(self, path, start_path):
        """Get the relative path between two paths.

        This function is actually a halfway implmentation of os.path.relname
        from python 2.6+. This version of the function will only work when
        path is a subdirectory of start_path and both are absolute paths when
        used with python <2.6.

        Args:
            path: Absolute path string to which to find the relative path
            start_path: The path string from which to find the relative path

        Return: Relative path string that leads from path to start_path.
        """
        if sys.version_info < (2, 6):
            return path[len(start_path):]

        return '/' + os.path.relpath(path, start_path)

    def normalize_target_id_in_build_file(self, target_id, build_file_path):
        """Normalize a target id found in a build file.

        Args:
            target_id: a TargetID found in a build file
            build_file_path: repository path of the build file in which this
                target was found
        """
        if target_id.is_normalized():
            return target_id

        path = self.normalize_path_in_build_file(target_id.path,
                build_file_path)
        name = target_id.name
        return digg.dev.hackbuilder.target.TargetID(path, name)

    def normalize_path_in_build_file(self, path, build_file_path):
        """Normalize a path found in a build file.

        Args:
            path: a path found in the build file
            build_file_path: repository path of the build file in which this
                target was found
        """
        if path == '':
            return build_file_path
        else:
            return os.path.join(build_file_path, path)


class TargetID(object):
    target_id_re = re.compile(r'^(?P<path>[^:]*)(:(?P<name>[^:]+))?$')

    def __init__(self, path, name):
        if path.find(':') != -1:
            raise digg.dev.hackbuilder.errors.TargetIDValueError(
                    'Target id path (%s) cannot contain a colon.'
                    % path)
        if path.endswith('/') and len(path) > 1:
            raise digg.dev.hackbuilder.errors.TargetIDValueError(
                    'Target id path (%s) cannot end in "/" if not root of '
                    'repository..'
                    % path)
        if name.find(':') != -1:
            raise digg.dev.hackbuilder.errors.TargetIDValueError(
                    'Target id name (%s) cannot contain a colon.'
                    % name)
        self.path = path
        self.name = name

        if self.has_name():
            self.id_string = '%s:%s' % (self.path, self.name)
        else:
            self.id_string = self.path

    @classmethod
    def from_string(cls, id_string):
        target_parts = cls.target_id_re.search(id_string)
        if target_parts is None:
            raise digg.dev.hackbuilder.errors.Error(
                    'Invalid target id string: %s'
                    % id_string)

        path = target_parts.group('path')
        name = target_parts.group('name')
        if name is None:
            name = ''
        return TargetID(path, name)

    def __eq__(self, other):
        return self.id_string == other.id_string

    def __hash__(self):
        return hash(self.id_string)

    def __str__(self):
        return self.id_string

    def __repr__(self):
        return "TargetID('%s')" % (self.id_string,)

    def is_absolute(self):
        return self.id_string.startswith('/')

    def is_relative(self):
        return not self.is_absolute()

    def is_path_only(self):
        return self.name == ''

    def has_name(self):
        return not self.is_path_only()

    def is_normalized(self):
        return self.is_absolute() and self.has_name()


class Target(object):
    def __init__(self, dep_ids=None):
        self.dep_ids = dep_ids

    def get_transitive_deps(self, build_target_resolver):
        transitive_deps = {}
        for dep_id in self.dep_ids:
            build_target = build_target_resolver.resolve(dep_id)
            transitive_deps.update({
                    build_target: build_target.get_transitive_deps(
                        build_target_resolver)
                    })
        return transitive_deps

    def __eq__(self, other):
        return self.target_id == other.target_id

    def __hash__(self):
        return hash(self.target_id)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.target_id.id_string)


class RunTarget(Target):
    """Run target.

    This target is a target that runs a binary.
    """

    def __init__(self, normalizer, target_id):
        if not target_id.is_normalized():
            raise digg.dev.hackbuilder.errors.TargetIDNotNormalizedError(
                    target_id)
        self.normalizer = normalizer
        self.target_id = target_id
        build_file_reader = (
                    digg.dev.hackbuilder.build.BuildFileReader(normalizer))
        self.build_target_resolver = (
                digg.dev.hackbuilder.build.BuildTargetFromBuildFileResolver(
                    build_file_reader))
        target = self.build_target_resolver.resolve(target_id)
        super(RunTarget, self).__init__([target_id])

    def run(self, args):
        logging.info('Running target: %s', self.target_id)
        target = self.build_target_resolver.resolve(self.target_id)
        all_args = [target.bin_path] + args
        command_string = '"{0}"'.format('" "'.join(all_args))
        logging.info('Execing command: %s', command_string)
        os.execv(target.bin_path, all_args)


class BuildTarget(Target):
    def __init__(self, normalizer, target_id, dep_ids=None):
        super(BuildTarget, self).__init__(dep_ids)
        if not target_id.is_normalized():
            raise digg.dev.hackbuilder.errors.TargetIDNotNormalizedError(
                    target_id)
        self.normalizer = normalizer
        self.target_id = target_id

        self.working_copy_root = self.normalizer.repo_root_path

        self.target_working_copy_dir = os.path.join(
                self.normalizer.repo_root_path,
                self.target_id.path[1:])

        self.source_root = os.path.join(
                self.normalizer.repo_root_path,
                digg.dev.hackbuilder.common.DEFAULT_SOURCE_DIR)

        self.target_source_dir = os.path.join(
                self.normalizer.repo_root_path,
                digg.dev.hackbuilder.common.DEFAULT_SOURCE_DIR,
                self.target_id.path[1:])

        self.build_root = os.path.join(
                self.normalizer.repo_root_path,
                digg.dev.hackbuilder.common.DEFAULT_BUILD_DIR)

        self.target_build_dir = os.path.join(
                self.normalizer.repo_root_path,
                digg.dev.hackbuilder.common.DEFAULT_BUILD_DIR,
                self.target_id.path[1:],
                '-' + self.target_id.name)

        self.package_root = os.path.join(
                self.normalizer.repo_root_path,
                digg.dev.hackbuilder.common.DEFAULT_PACKAGE_DIR)


class BinaryLauncherBuildTarget(BuildTarget):
    pass


class StartScriptBuildTarget(BinaryLauncherBuildTarget):
    pass


class PackageBuildTarget(BuildTarget):
    pass


class BinaryBuildTarget(BinaryLauncherBuildTarget):
    pass


class LibraryBuildTarget(BuildTarget):
    pass
