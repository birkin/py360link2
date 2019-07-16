# -*- coding: utf-8 -*-

"""
Tests for handling OpenURLs with 360Link.

For these to run, a Serial Solutions 360Link XML API key must be
supplied.
"""

import logging, os, pprint, sys, unittest
from urllib.parse import parse_qs
# from py360link2 import get_sersol_data, Resolved
try:
    from py360link2 import get_sersol_data, Resolved
except:
    sys.path.append( '../' )  # accessed when running, eg, `python ./openurl.py TestFromOpenURL.test_unicode_dump`
    from py360link2 import get_sersol_data, Resolved


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s', datefmt='%d/%b/%Y %H:%M:%S' )
log = logging.getLogger( 'py360link2' )


#A 360Link API key needs to be specified here.
KEY = os.environ['PY360LINK2__TEST_KEY']

class TestPmidLookup(unittest.TestCase):
    """
    Test a simple lookup by Pubmed ID.
    """
    def setUp(self):
        ourl = 'id=pmid:19282400&sid=Entrez:PubMed'
        data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(data)

    # def test_get_sersol_data_types(self):
    #     """ Checks for unicode data in initially retrieved data. """
    #     self.assertEqual( 1, 2 )

    def test_link_groups(self):
        """
        These will depend from institution to institution so just check for keys.
        """
        link_groups = self.sersol.link_groups
        required = ['url', 'holdingData', 'type']
        for link in link_groups:
            for req in required:
                # self.assertTrue(link.has_key(req))
                self.assertTrue( req in link.keys() )

    def test_citation(self):
        citation = self.sersol.citation
        self.assertEqual(citation['creator'], 'Moriya, T')
        self.assertEqual(citation['doi'], '10.1177/1753193408098482')
        self.assertEqual(citation['volume'], '34')
        self.assertEqual(citation['spage'], '219')
        self.assertTrue(citation['title'].rfind('Effect of triangular') > -1)

    def test_citation_types(self):
        """ Checks for unicode keys and values in citation. """
        citation = self.sersol.citation
        pprint.pprint( citation.items() )
        for ( key, val ) in citation.items():
            if type( val ) == dict:
                for (subkey, subval ) in val.items():
                    self.assertEqual( type(subkey), str )
                    self.assertEqual( type(subval), str )
            else:
                self.assertEqual( type(key), str )
                self.assertEqual( type(val), str )

    def test_openurl(self):
        """
        We can round trip this to see if the original request is enhanced by
        the results of the 360Link resolution.
        """
        ourl = self.sersol.openurl
        ourl_dict = parse_qs(ourl)
        self.assertEqual(ourl_dict['rft_id'], ['info:doi/10.1177/1753193408098482', 'info:pmid/19282400'])
        self.assertEqual(ourl_dict['rft.eissn'][0], '2043-6289')
        # print ourl
        log.debug( f'ourl, ```{ourl}```' )

    def test_openurl_types(self):
        """ Checks for unicode keys and values in parsed openurl. """
        ourl = self.sersol.openurl
        self.assertEqual( type(ourl), str )

    ## end class TestPmidLookup()


class TestDoiLookup(unittest.TestCase):
    def setUp(self):
        ourl = 'rft_id=info:doi/10.1016/j.neuroimage.2009.12.024'
        data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(data)

    def test_citation(self):
        citation = self.sersol.citation
        self.assertEqual(citation['creator'], 'Berman, Marc G.')
        self.assertEqual(citation['doi'], '10.1016/j.neuroimage.2009.12.024')
        self.assertEqual(citation['volume'], '50')
        self.assertEqual(citation['spage'], '56')
        self.assertTrue(citation['title'].rfind('Evaluating functional localizers') > -1)

    def test_echoed_query(self):
        qdict = self.sersol.query_dict
        self.assertEqual(qdict['rft_id'][0], 'info:doi/10.1016/j.neuroimage.2009.12.024')
        #Basic check, these are defaults.
        self.assertEqual(qdict['url_ver'][0], 'Z39.88-2004')
        self.assertEqual(qdict['version'][0], '1.0')

class TestCiteLookup(unittest.TestCase):
    def setUp(self):
        ourl = 'title=Organic%20Letters&date=2008&issn=1523-7060&issue=19&spage=4155'
        self.data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(self.data)

    def test_citation(self):
        citation = self.sersol.citation
        self.assertEqual(citation['source'], 'Organic letters')
        self.assertEqual(citation['date'], '2008')

    def test_echoed_query(self):
        qdict = self.sersol.query_dict
        self.assertEqual(qdict['title'][0], 'Organic Letters')
        self.assertEqual(qdict['date'][0], '2008')

    def test_openurl(self):
        """
        Check for the enhanced data.
        """
        ourl = self.sersol.openurl
        ourl_dict = parse_qs(ourl)
        self.assertEqual(ourl_dict['rft.eissn'][0], '1523-7052')

class TestFirstSearchBookLookup(unittest.TestCase):
    def setUp(self):
        #Sample passed from OCLC
        ourl = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9780394565279&title=The+risk+pool&date=1988&aulast=Russo&aufirst=Richard&id=doi%3A&pid=%3Caccession+number%3E17803510%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E17803510%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F17803510&rft_id=urn%3AISBN%3A9780394565279&rft.aulast=Russo&rft.aufirst=Richard&rft.btitle=The+risk+pool&rft.date=1988&rft.isbn=9780394565279&rft.place=New+York&rft.pub=Random+House&rft.edition=1st+ed.&rft.genre=book&checksum=d6c1576188e0f87ac13f4c4582382b4f&title=Brown University&linktype=openurl&detail=RBN'
        self.data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(self.data)

    def test_link360_resolved(self):
        citation = self.sersol.citation
        self.assertEqual(self.sersol.format, 'book')
        self.assertEqual(citation['title'], 'The risk pool')
        self.assertTrue('9780394565279' in citation['isbn'])

    def test_openurl(self):
        ourl = self.sersol.openurl
        ourl_dict = parse_qs(ourl)
        self.assertTrue(ourl_dict['rfe_dat'][0], '<accessionnumber>17803510</accessionnumber>')
        #simple string find for accession number
        self.assertTrue(ourl.rfind('17803510') > -1 )

class TestFirstSearchArticleLookup(unittest.TestCase):
    def setUp(self):
        #Sample passed from OCLC
        ourl = 'sid=FirstSearch%3AMEDLINE&genre=article&issn=0037-9727&atitle=Serum+and+urine+chromium+as+indices+of+chromium+status+in+tannery+workers.&title=Proceedings+of+the+Society+for+Experimental+Biology+and+Medicine.+Society+for+Experimental+Biology+and+Medicine+%28New+York%2C+N.Y.%29&volume=185&issue=1&spage=16&epage=23&date=1987&aulast=Randall&aufirst=JA&sici=0037-9727%28198705%29185%3A1%3C16%3ASAUCAI%3E2.0.TX%3B2-3&id=doi%3A&pid=%3Caccession+number%3E114380499%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AMEDLINE&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E114380499%3C%2Faccessionnumber%3E&rft_id=urn%3AISSN%3A0037-9727&rft.aulast=Randall&rft.aufirst=JA&rft.atitle=Serum+and+urine+chromium+as+indices+of+chromium+status+in+tannery+workers.&rft.jtitle=Proceedings+of+the+Society+for+Experimental+Biology+and+Medicine.+Society+for+Experimental+Biology+and+Medicine+%28New+York%2C+N.Y.%29&rft.date=1987&rft.volume=185&rft.issue=1&rft.spage=16&rft.epage=23&rft.issn=0037-9727&rft.genre=article&rft.sici=0037-9727%28198705%29185%3A1%3C16%3ASAUCAI%3E2.0.TX%3B2-3&checksum=2a13709e5b9664e62d31e421f6f77c94&title=Brown University&linktype=openurl&detail=RBN'
        self.data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(self.data)

    def test_link360_resolved(self):
        pprint.pprint(self.data)
        citation = self.sersol.citation
        self.assertEqual(self.sersol.format, 'journal')
        self.assertEqual(citation['title'], 'Serum and urine chromium as indices of chromium status in tannery workers.')
        self.assertTrue('1525-1373' in citation['eissn'])

    def test_openurl(self):
        ourl = self.sersol.openurl
        ourl_dict = parse_qs(ourl)
        self.assertTrue(ourl_dict['rft.genre'][0], 'article')
        self.assertTrue(ourl_dict['rfe_dat'][0], '<accessionnumber>114380499</accessionnumber>')
        #simple string find for accession number
        self.assertTrue(ourl.rfind('114380499') > -1 )


class TestUnicodeOpenUrlLookup( unittest.TestCase ):

    def setUp(self):
        ourl = 'url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Adissertation&rft.genre=dissertation&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E699516442%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F699516442&rft.aulast=Amado+Gonzales&rft.aufirst=Donato&rft.title=El+cabildo+de+los+veinticuatro+electores+del+Alfe%CC%81rez+Real+Inca+de+las+parroquias+cuzquen%CC%83as&rft.date=2010&rfe_dat=%3Cdissnote%3ETesis+%28Mag.%29--Pontificia+Universidad+Cato%CC%81lica+del+Peru%CC%81.+Escuela+de+Graduados.+Mencio%CC%81n%3A+Historia.%3C%2Fdissnote%3E'
        self.data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(self.data)

    def test_openurl(self):
        ourl = self.sersol.openurl
        ourl_dict = parse_qs(ourl)
        self.assertEqual( ourl_dict['rft.genre'][0], 'article' )
        self.assertEqual( ourl_dict['rfe_dat'][0], '<accessionnumber>699516442</accessionnumber>' )
        # self.assertEqual( ourl_dict['rfe_dat'][1], '<dissnote>Tesis (Mag.)--Pontificia Universidad Cato\xcc\x81lica del Peru\xcc\x81. Escuela de Graduados. Mencio\xcc\x81n: Historia.</dissnote>' )
        self.assertEqual( ourl_dict['rfe_dat'][1], b'<dissnote>Tesis (Mag.)--Pontificia Universidad Cato\xcc\x81lica del Peru\xcc\x81. Escuela de Graduados. Mencio\xcc\x81n: Historia.</dissnote>'.decode('utf-8') )




if __name__ == '__main__':
    unittest.main()

