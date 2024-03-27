import unittest

from test.splitter.html_tag_splitter_test import HtmlTagSplitterTest
from test.splitter.moving_window_splitter_test import MovingWindowSplitterTest
from test.splitter.recursive_character_text_splitter_test import RecursiveCharacterSplitterTest


def suite():
    loader = unittest.TestLoader()

    test_suite = unittest.TestSuite()
    test_suite.addTest(loader.loadTestsFromTestCase(HtmlTagSplitterTest))
    test_suite.addTest(loader.loadTestsFromTestCase(MovingWindowSplitterTest))
    test_suite.addTest(loader.loadTestsFromTestCase(RecursiveCharacterSplitterTest))

    return test_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
