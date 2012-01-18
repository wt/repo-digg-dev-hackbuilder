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

import unittest

import digg.dev.hackbuilder.errors
import digg.dev.hackbuilder.target

class TargetTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        target_id = digg.dev.hackbuilder.target.TargetID('/lev1', 'blah')
        self.assertEqual(target_id.path, '/lev1')
        self.assertEqual(target_id.name, 'blah')

    def test_absolute_target_id_with_path_with_name_normalized(self):
        target_id = digg.dev.hackbuilder.target.TargetID.from_string(
                '/lev1/lev2:blah')
        self.assertEqual(str(target_id), '/lev1/lev2:blah')
        self.assertEqual(target_id.path, '/lev1/lev2')
        self.assertEqual(target_id.name, 'blah')
        self.assertTrue(target_id.is_absolute())
        self.assertFalse(target_id.is_relative())
        self.assertFalse(target_id.is_path_only())
        self.assertTrue(target_id.has_name())

    def test_relative_target_id_with_path_with_name(self):
        target_id = digg.dev.hackbuilder.target.TargetID.from_string(
                '../lev2:blah')
        self.assertEqual(str(target_id), '../lev2:blah')
        self.assertEqual(target_id.path, '../lev2')
        self.assertEqual(target_id.name, 'blah')
        self.assertFalse(target_id.is_absolute())
        self.assertTrue(target_id.is_relative())
        self.assertFalse(target_id.is_path_only())
        self.assertTrue(target_id.has_name())

    def test_relative_target_id_without_path_with_name(self):
        target_id = digg.dev.hackbuilder.target.TargetID.from_string(':blah')
        self.assertEqual(str(target_id), ':blah')
        self.assertEqual(target_id.path, '')
        self.assertEqual(target_id.name, 'blah')
        self.assertFalse(target_id.is_absolute())
        self.assertTrue(target_id.is_relative())
        self.assertFalse(target_id.is_path_only())
        self.assertTrue(target_id.has_name())

    def test_absolute_target_id_with_path_without_name(self):
        target_id = digg.dev.hackbuilder.target.TargetID.from_string('/lev1/lev2')
        self.assertEqual(str(target_id), '/lev1/lev2')
        self.assertEqual(target_id.path, '/lev1/lev2')
        self.assertEqual(target_id.name, '')
        self.assertTrue(target_id.is_absolute())
        self.assertFalse(target_id.is_relative())
        self.assertTrue(target_id.is_path_only())
        self.assertFalse(target_id.has_name())

    def test_relative_target_id_with_path_without_name(self):
        target_id = digg.dev.hackbuilder.target.TargetID.from_string('../lev2')
        self.assertEqual(str(target_id), '../lev2')
        self.assertEqual(target_id.path, '../lev2')
        self.assertEqual(target_id.name, '')
        self.assertFalse(target_id.is_absolute())
        self.assertTrue(target_id.is_relative())
        self.assertTrue(target_id.is_path_only())
        self.assertFalse(target_id.has_name())

    def test_absolute_target_path_with_trailing_slash(self):
        self.assertRaises(digg.dev.hackbuilder.errors.TargetIDValueError,
                digg.dev.hackbuilder.target.TargetID, '/testdir/', 'testname')

    def test_relative_target_path_with_trailing_slash(self):
        self.assertRaises(digg.dev.hackbuilder.errors.TargetIDValueError,
                digg.dev.hackbuilder.target.TargetID, 'testdir/', 'testname')


class NormalizerTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_normalize_relative_path(self):
        normalizer = digg.dev.hackbuilder.target.Normalizer('.')
        target_id = normalizer.normalize_path('lev2')
        self.assertEqual(target_id, '/lev2')


def main():
    unittest.main(__name__)

if __name__ == '__main__':
    main()
