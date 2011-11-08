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

class Error(Exception):
    """Base exception for all errors in this module."""


class TargetIDNotNormalizedError(Error):
    """Exception for improper use of non-normalized target id."""
    def __init__(self, target_id):
        self.target_id = target_id

    def __str__(self):
        return 'Target ID not normalized: %s' % (self.target_id)


class TargetIDValueError(Error):
    """Exception for invalid values for target ids."""
