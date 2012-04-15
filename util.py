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
import os
import os.path

import digg.dev.hackbuilder.errors

def get_root_of_repo_directory_tree(path='.'):
    """Find the root of the repository.

    This function works by looking for a .repo directory in the current
    directory. If that fails, it looks in each parent directory for the .repo
    directory.

    Note: This function will very likely not work on Microsoft Windows.

    Args:
        path: The path of where to start looking for the top of the
        repository. This defaults to the current directory.

    Raises:
        digg.dev.hackbuilder.errors.Error: When the root directory is reached
        before finding the root of the repository or when .repo is not a
        directory.
    """
    current_path = path
    while True:
        filenames = os.listdir(current_path)
        if '.repo' in filenames:
            repo_path = os.path.join(current_path, '.repo')
            if not os.path.isdir(repo_path):
                raise digg.dev.hackbuilder.errors.Error(
                        'The .repo path (%s) is not a directory.' %
                        (repo_path,))
            break
        if os.path.abspath(current_path) == '/':
            raise digg.dev.hackbuilder.errors.Error(
                    'Root of repository not found. Stopped looking at root.')
        current_path = os.path.join(current_path, '..')

    return os.path.abspath(current_path)


def mirror_filesystem_hierarchy(from_path, to_path):
    """Create symlinked file hierarchy.

    This function will mirror a filesystem hierarchy into the to_path from the
    from_path. The directory hierarchy will be handled my creating directories
    in a mirror image of the directories in the from_path. The other files will
    be symlinks from their location in the from_path to the location in the
    to_path.

    Args:
        from_path: the filesystem path of the root of the source location to
                mirror
        to_path: the filesystem path of the root to where the source hierarchy
                will be mirrored
    """
    logging.debug('Mirroring filesystem hierarchy from (%s) to (%s).',
            from_path, to_path)
    for path, subdirs, filenames in os.walk(from_path):
        # make directories
        logging.debug('Path: %s', path)
        for subdir in subdirs:
            rel_dir = os.path.relpath(os.path.join(path, subdir), from_path)
            full_to_path = os.path.join(to_path, rel_dir)
            try:
                os.makedirs(full_to_path)
                logging.debug('Made directory: %s', full_to_path)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise
                logging.debug('Directory already existed: %s', full_to_path)

        # make symlinks
        logging.debug('Files: %s', filenames)
        for filename in filenames:
            rel_file_path = os.path.relpath(
                    os.path.join(path, filename), from_path)
            full_from_path = os.path.join(from_path, rel_file_path)
            full_to_path = os.path.join(to_path, rel_file_path)
            rel_from_path = os.path.relpath(full_from_path,
                    os.path.dirname(full_to_path))
            try:
                os.symlink(rel_from_path, full_to_path)
                logging.debug('Symlinked %s to %s.', full_to_path,
                        rel_from_path)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise
                logging.debug('File already existed: %s', full_to_path)
                if os.readlink(full_to_path) != rel_from_path:
                    logging.debug('Symlink incorrect. Removing and '
                            'symlinking %s to %s', full_to_path, rel_from_path)
                    os.remove(full_to_path)
                    os.symlink(rel_from_path, full_to_path)
