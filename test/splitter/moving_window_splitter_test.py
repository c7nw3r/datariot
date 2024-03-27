from unittest import TestCase

from datariot.splitter import MovingWindowSplitter

WIKIPEDIA_TEXT = """The Wikimedia Foundation, Inc., abbreviated WMF, is an
American 501(c)(3) nonprofit organization
headquartered in San Francisco, California, and
registered there as a charitable foundation. It is
best known as the host of Wikipedia, the seventh most
visited website in the world. However, the foundation
also hosts 14 other related content projects. It also
supports the development of MediaWiki, the wiki
software that underpins them all.The Wikimedia
Foundation was established, in 2003 in St. Petersburg,
Florida, by Jimmy Wales as a nonprofit way to fund
Wikipedia, Wiktionary, and other crowdsourced wiki
projects. (Until then, they had been hosted by Bomis,
Wales's for-profit company.) The Foundation finances
itself mainly through millions of small donations from
Wikipedia readers, collected through email campaigns
and annual fundraising banners placed on Wikipedia and
its sister projects. These are complemented by grants
from philanthropic organizations and tech companies,
and starting in 2022, by services income from
Wikimedia Enterprise."""


class MovingWindowSplitterTest(TestCase):

    def test_split(self):
        splitter = MovingWindowSplitter(100, 5)
        self.assertEqual(len(splitter(WIKIPEDIA_TEXT)), 12)
