import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('release', pathlib.Path(__file__).resolve().parents[1] / 'scripts/release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EditorialReleaseTests(unittest.TestCase):
    def catalog(self):
        return {'edition': 'old', 'groups': [{'id': 'a', 'name': '甲组', 'current': '通信', 'revision': 2, 'logs': []}]}

    def test_first_edition_is_baseline(self):
        output = module.release(self.catalog(), {}, 'new')
        self.assertFalse(output['groups'][0]['updatedThisEdition'])
        self.assertEqual(output['groups'][0]['revision'], 1)

    def test_no_change_clears_round_badge_without_changing_unread_version(self):
        previous = self.catalog()
        previous['groups'][0]['updatedThisEdition'] = True
        output = module.release(previous, previous, 'new')
        self.assertFalse(output['groups'][0]['updatedThisEdition'])
        self.assertEqual(output['groups'][0]['revision'], 2)

    def test_verified_change_advances_only_affected_group(self):
        previous = self.catalog()
        catalog = self.catalog()
        catalog['groups'][0]['current'] = '通信与感知'
        output = module.release(catalog, previous, 'new')
        self.assertTrue(output['groups'][0]['updatedThisEdition'])
        self.assertEqual(output['groups'][0]['revision'], 3)
        self.assertEqual(previous['groups'][0]['revision'], 2)

    def test_check_timestamp_alone_is_not_news(self):
        previous = self.catalog()
        catalog = self.catalog()
        catalog['groups'][0]['evidenceDate'] = '2026-11-05'
        output = module.release(catalog, previous, 'new')
        self.assertEqual(output['changedGroupIds'], [])

    def test_new_group_after_baseline_is_news(self):
        previous = self.catalog()
        catalog = self.catalog()
        catalog['groups'].append({'id': 'b', 'name': '乙组', 'logs': []})
        output = module.release(catalog, previous, 'new')
        self.assertTrue(output['groups'][1]['updatedThisEdition'])
        self.assertEqual(output['groups'][1]['revision'], 1)


if __name__ == '__main__':
    unittest.main()
