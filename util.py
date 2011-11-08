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

import os
import os.path

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
        if current_path == '/':
            raise digg.dev.hackbuilder.errors.Error(
                    'Root of repository not found. Stopped looking at root.')
        current_path = os.path.join(current_path, '..')

    return current_path
