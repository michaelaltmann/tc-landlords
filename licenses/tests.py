from django.test import TestCase
from transform import cleanName

import unittest


class TestCleanName(unittest.TestCase):
    def testLower(self):
        self.assertEqual(cleanName('This is A test'), 'this is a test')

    def testLLC(self):
        self.assertEqual(cleanName('cat llLLC'), 'cat llllc')
        self.assertEqual(cleanName('Llama LLC'), 'llama')
        self.assertEqual(cleanName('Frog, LC'), 'frog')
        self.assertEqual(cleanName('LLC Baboon, LlC'), 'llc baboon')
        self.assertEqual(cleanName('229 Queen Rental LLC'), '229 queen rental')

    def testSpaces(self):
        self.assertEqual(cleanName('   a  b  c  '), 'a b c')


if __name__ == '__main__':
    unittest.main()
