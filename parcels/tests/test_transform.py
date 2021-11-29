from parcels.transform import cleanName
import pandas as pd
import pytest


class TestCleanName:
    def testLower(self):
        assert cleanName('This is A test') == 'this is a test'

    def testPunctuation(self):
        assert cleanName('a . ... -; ;; ,z') == 'a z'


    def testLLC(self):
        assert cleanName('cat llLLC') == 'cat llllc'
        assert cleanName('Llama LLC') == 'llama'
        assert cleanName('Llama, LLC') == 'llama'
        assert cleanName('Llama L.L.C') == 'llama'
        assert cleanName('Frog, LC') == 'frog'
        assert cleanName('bird, L.   L.   C.   ') == 'bird'
        assert cleanName('Frog, L. L. C.') == 'frog'
        assert cleanName('Garfield apt') == 'garfield apartments'
        assert cleanName('Emerson apts and condos') == 'emerson apartments and condos'
        assert cleanName('LLC Baboon, LlC') == 'llc baboon'
        assert cleanName('229 Queen Rental LLC') == '229 queen rental'

    def testSpaces(self):
        assert cleanName('   a  b  c  '), 'a b c'


class TestOwnerOrApplication:
    def testMissingOwnerPhone(self):
        data = [['tom', None], [None, 'sally'], [None, None]]
        df = pd.DataFrame(data, columns=['owner', 'applicant'])
        df['best'] = df['owner'].fillna(df['applicant'])
        assert df.iloc[0]['best'] == 'tom'
        assert df.iloc[1]['best'] == 'sally'
        assert df.iloc[2]['best'] == None


class TestCleanPhone():
    def testCleanPhone(self):
        data = [['6125551212'], ['(612)5551212'], [' (612) 555-12.12']]
        df = pd.DataFrame(data, columns=['phone'])
        df['xPhone'] = df['phone'].str.replace(r"[\(\)\-\.\s]", "", regex=True)
        assert df['xPhone'].eq('6125551212').all()


