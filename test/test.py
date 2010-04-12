#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest, sys, tumbkit


class MainTestCase(unittest.TestCase):
    """ a couple of integration tests """
    
    def setUp(self):
        tumbkit.engine = tumbkit.Engine('./tpl.html', './cfg.json')

    def tearDown(self):
        tumbkit.engine = None
        
    def test_post(self):
        self.assert_(tumbkit.post('489880838', ''))

    def test_index(self):
        self.assert_(tumbkit.index())
        self.assert_(tumbkit.index('2'))
        
    def test_search(self):
        self.assert_(tumbkit.search('test'))
        self.assert_(tumbkit.search('test', '2'))
        self.assert_(tumbkit.search('noresult'))
        
    def test_tagged(self):
        self.assert_(tumbkit.tagged('ipsum'))
        
    def test_day(self):
        self.assert_(tumbkit.day('2010', '04', '01'))


def run():
    suite = unittest.TestLoader().loadTestsFromTestCase(MainTestCase)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    sys.exit((result.errors or result.failures) and 1 or 0)


if __name__ == '__main__':
    run()
    
