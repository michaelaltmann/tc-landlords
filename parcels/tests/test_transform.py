from parcels.transform import cleanName, cleanAddressLine, cleanPhone, cleanPhone
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
        assert cleanPhone('6125551212') == '612.555.1212'
        assert cleanPhone('612555 1212') == '612.555.1212'
        assert cleanPhone('6125551212x999') == '612.555.1212'
        assert cleanPhone('(612)555-1212') == '612.555.1212'
        assert cleanPhone('5551212') == '555.1212'
        assert cleanPhone('12345') == '12345'
        


class TestCleanAddress():
    def testCleanAddress(self):
        assert cleanAddressLine('55410') == '55410'
        assert cleanAddressLine('55410-0000') == '55410'
        assert cleanAddressLine('55-56') == '55-56'
        assert cleanAddressLine('55410-00x00') == '55410-00X00'
        assert cleanAddressLine('55410-00x00') == '55410-00X00'
        assert cleanAddressLine('123   ,Main ST') == '123 MAIN STREET'