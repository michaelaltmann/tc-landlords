from django.test import TestCase
from licenses.transform import cleanName
import pandas as pd
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


class TestOwnerOrApplication(unittest.TestCase):
    def testMissingOwnerPhone(self):
        data = [['tom', None], [None, 'sally'], [None, None]]
        df = pd.DataFrame(data, columns=['owner', 'applicant'])
        df['best'] = df['owner'].fillna(df['applicant'])
        self.assertEqual(df.iloc[0]['best'], 'tom')
        self.assertEqual(df.iloc[1]['best'], 'sally')
        self.assertEqual(df.iloc[2]['best'], None)


class TestCleanPhone(unittest.TestCase):
    def testCleanPhone(self):
        data = [['6125551212'], ['(612)5551212'], [' (612) 555-12.12']]
        df = pd.DataFrame(data, columns=['phone'])
        df['xPhone'] = df['phone'].str.replace(r"[\(\)\-\.\s]", "", regex=True)
        self.assertTrue(df['xPhone'].eq('6125551212').all())


if __name__ == '__main__':
    unittest.main()
