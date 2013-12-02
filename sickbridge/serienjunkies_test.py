import unittest

from serienjunkies import parse_episode_no

class TestEpisodeNo(unittest.TestCase):
    def test_simple_names(self):
		self.assertEqual((1, 14), parse_episode_no("Ultimate.SpiderMan.S01E14.Awesome.HDTV.XviD"))

if __name__ == '__main__':
    unittest.main()