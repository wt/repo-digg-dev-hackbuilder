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

import errno
import logging
import os.path

import digg.dev.hackbuilder.target


def normal_dep_targets_from_dep_strings(repo_path, normalizer, deps):
    normalized_deps = set()
    for dep in deps:
        orig_dep_id = digg.dev.hackbuilder.target.TargetID.from_string(
                dep)
        new_dep_id = normalizer.normalize_target_id_in_build_file(
                orig_dep_id, repo_path)
        normalized_deps.add(new_dep_id)

    return normalized_deps


class Builder(object):
    def __init__(self, target):
        self.normalizer = target.normalizer
        self.target = target

    def do_create_source_tree_work(self):
        pass

    def do_create_build_environment_work(self):
        pass

    def do_build_binary_work(self):
        pass

    def do_build_package_work(self):
        pass


class PackageBuilder(Builder):
    pass


class BinaryBuilder(Builder):
    pass


class LibraryBuilder(Builder):
    def do_create_source_tree_work(self):
        logging.info('Copying %s into source tree', self.target.target_id)
        for filename in self.target.files:
            src_filename = os.path.join(self.target.target_working_copy_dir, filename)
            dest_filename = os.path.join(self.target.target_source_dir, filename)

            try:
                dest_dirname = os.path.dirname(dest_filename)
                os.makedirs(dest_dirname)
                logging.debug('Created directory: %s', dest_dirname)
            except OSError, e:
                if not e.errno == errno.EEXIST:
                    raise
                else:
                    logging.debug('Directory already exists: %s', dest_dirname)
            try:
                rel_from_path = os.path.relpath(src_filename,
                        os.path.dirname(dest_filename))
                os.symlink(rel_from_path, dest_filename)
                logging.debug('Symlinked %s to %s.', rel_from_path,
                        dest_filename)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise
                logging.debug('File already existed: %s', dest_filename)
                if os.readlink(dest_filename) != rel_from_path:
                    logging.debug('Symlink incorrect. Removing and '
                            'symlinking %s to %s', rel_from_path, dest_filename)
                    os.remove(dest_filename)
                    os.symlink(rel_from_path, dest_filename)
