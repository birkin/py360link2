# -*- coding: utf-8 -*-


import json, io, logging, pprint, re, sys, urllib
assert sys.version_info.major > 2
from urllib.parse import parse_qs

import requests
from lxml import etree


#Added to avoid the following errors:
#Cannot convert lxml.etree._RotatingErrorLog to lxml.etree._BaseErrorLog
class Logger(etree.PyErrorLog):
    def log(self, entry, message, *args):
        pass
etree.use_global_python_log(Logger())


logging.basicConfig(
    filename='', level='DEBUG',
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S'
    )
logger = logging.getLogger(__name__)
logger.debug( 'link360.py START' )


SERSOL_KEY = None

#Make the OpenURL for passing on.
SERSOL_MAP = {
    'journal': {
        'title': 'atitle',
        'creatorLast': 'aulast',
        'creator': 'au',
        'creatorFirst': 'aufirst',
        'creatorMiddle': 'auinitm',
        'source': 'jtitle',
        'date': 'date',
        #issns are tricky - handle in application logic
        'issn': 'issn',
        'eissn': 'eissn',
        'isbn': 'isbn',
        'volume': 'volume',
        'issue': 'issue',
        'spage': 'spage',
        #dois and pmids need to be handled differently too.
        #This mapping is here just to retain their original keys.
        'doi': 'doi',
        'pmid': 'pmid',
        #'publisher': 'publisher'
        #publicationPlace
        },
    'book': {
        'publisher': 'pub',
        'isbn': 'isbn',
        'title': 'btitle',
        'date': 'date',
        'creator': 'author',
        'creatorLast': 'aulast',
        'creatorLast': 'aulast',
        'creatorFirst': 'aufirst',
        'creatorMiddle': 'auinitm',
        'isbn': 'isbn',
        'title': 'btitle',
        'date': 'date',
        'publicationPlace': 'place',
        'format': 'genre',
        'source': 'btitle',
    }
}

class Link360Exception(Exception):
    def __init__self(self, message, Errors):
        #http://stackoverflow.com/questions/1319615/proper-way-to-declare-custom-exceptions-in-modern-python
        Exception.__init__(self, message)
        self.Errors = Errors


def get_sersol_response(query, key, timeout):
    """
    Get the SerSol API response and parse it into an etree.
    """
    if key is None:
        raise Link360Exception('Serial Solutions 360Link XML API key is required.')

    required_url_elements = {}
    required_url_elements['version'] = '1.0'
    required_url_elements['url_ver'] = 'Z39.88-2004'
    #Go get the 360link response
    #Base 360Link url
    base_url = "http://%s.openurl.xml.serialssolutions.com/openurlxml?" % key
    # base_url += urllib.urlencode(required_url_elements)  # python2
    base_url += urllib.parse.urlencode( required_url_elements )
    url = base_url + '&%s' % query.lstrip('?')
    r = requests.get( url )
    # filelike_obj = StringIO.StringIO( r.content )
    filelike_obj = io.BytesIO( r.content )
    doc = etree.parse( filelike_obj )
    return doc


def get_sersol_data(query, key=None, timeout=5):
    """
    Get and process the data from the API and store in Python dictionary.
    If you would like to cache the 360Link responses, this is data structure
    that you would like to cache.

    Specify a timeout for the http request to 360Link.

    Conversion to and from json is because `data` contains lxml _ElementStringResult elements,
    which can cause pickling problems.
    """
    logger.debug( 'starting get_sersol_data()' )
    if query is None:
        raise Link360Exception('OpenURL query required.')
    doc = get_sersol_response(query, key, timeout)
    data = Link360JSON(doc).convert()
    logger.debug( 'data, ```%s```' % pprint.pformat(data) )
    jsn = json.dumps( data )
    jdct = json.loads( jsn )
    # logger.debug( 'jdct, ```%s```' % pprint.pformat(jdct) )
    return jdct


class Link360JSON(object):
    """
    Convert Link360 XML To JSON
    follows http://xml.serialssolutions.com/ns/openurl/v1.0/ssopenurl.xsd
    Godmar Back <godmar@gmail.com>, May 2009
    """
    def __init__(self, doc):
        self.doc = doc

    def convert(self):

        logger.debug( 'starting convert' )

        ns = {
            "ss" : "http://xml.serialssolutions.com/ns/openurl/v1.0",
            "sd" : "http://xml.serialssolutions.com/ns/diagnostics/v1.0",
            "dc" : "http://purl.org/dc/elements/1.1/"
        }

        # def x(xpathexpr, root = self.doc):
        #     x_data = root.xpath(xpathexpr, namespaces=ns)
        #     # logger.debug( x_data )
        #     # if type(x_data) == list:
        #     #     if len( x_data ) > 0:
        #     #         logger.debug( 'type(x_data[0]), `%s`' % type(x_data[0]) )
        #     return x_data

        def x(xpathexpr, root=self.doc):
            """ Called by return m() """
            logger.debug( 'xpathexpr, ```%s```' % xpathexpr )
            x_data = root.xpath(xpathexpr, namespaces=ns)
            # logger.debug( x_data )
            # if type(x_data) == list:
            #     if len( x_data ) > 0:
            #         logger.debug( 'type(x_data[0]), `%s`' % type(x_data[0]) )
            logger.debug( 'initial x_data, ```%s```' % x_data )
            improved_x_data = []
            for element in x_data:
                if type(element) == str:
                    pass
                elif type( element ) == etree._ElementUnicodeResult:
                    pass
                elif type( element ) == etree._ElementStringResult:
                    element = element.decode( 'utf-8' )
                elif type( element ) == etree._Element:
                    logger.debug( 'hmmm, how to handle type(element), ```%s```?' % type(element) )
                    logger.debug( 'stringified, ```%s```' % etree.tostring(element) )
                else:
                    logger.debug( 'uh oh, type(element), ```%s```' % type(element) )
                improved_x_data.append( element )
            logger.debug( 'final x_data, ```%s```' % improved_x_data )
            return improved_x_data

        # def t(xpathexpr, root = self.doc):
        #     r = x(xpathexpr, root)
        #     if len(r) > 0:
        #         return r[0]
        #     return None

        def t( xpathexpr, root=self.doc ):
            return_val = None
            r = x(xpathexpr, root)
            if len(r) > 0:
                return_val = r[0]
            logger.debug( 'return_val, ```%s```' % return_val )
            if return_val:
                assert type(return_val) == str or type(return_val) == etree._ElementUnicodeResult, type(return_val)
            return return_val

        def m(dict, *kv):
            """merge (k, v) pairs into dict if v is not None"""
            for (k, v) in kv:
                if v:
                    dict[k] = v
            logger.debug( 'dict, ```%s```' % pprint.pformat(dict) )
            return dict

        return m({
            'version' : t("//ss:version/text()"),
            'echoedQuery' : {
                'queryString' : t("//ss:echoedQuery/ss:queryString/text()"),
                'timeStamp' : t("//ss:echoedQuery/@timeStamp"),
                'library' : {
                    'name' : t("//ss:echoedQuery/ss:library/ss:name/text()"),
                    'id' : t("//ss:echoedQuery/ss:library/@id")
                }
            },
            'dbDate' : t("//ss:results/@dbDate"),
            'results' : [ {
                'format' : t("./@format", result),
                'citation' : m({ },
                    ('title', t(".//dc:title/text()")),
                    ('creator', t(".//dc:creator/text()")),
                    ('source', t(".//dc:source/text()")),
                    ('date', t(".//dc:date/text()")),
                    ('publisher', t(".//dc:publisher/text()")),
                    ('creatorFirst', t(".//ss:creatorFirst/text()")),
                    ('creatorMiddle', t(".//ss:creatorMiddle/text()")),
                    ('creatorLast', t(".//ss:creatorLast/text()")),
                    ('volume', t(".//ss:volume/text()")),
                    ('issue', t(".//ss:issue/text()")),
                    ('spage', t(".//ss:spage/text()")),
                    ('doi', t(".//ss:doi/text()")),
                    ('pmid', t(".//ss:pmid/text()")),
                    ('publicationPlace', t(".//ss:publicationPlace/text()")),
                    ('institution', t(".//ss:institution/text()")),
                    ('advisor', t(".//ss:advisor/text()")),
                    ('patentNumber', t(".//ss:patentNumber/text()")),
                    # assumes at most one ISSN per type
                    ('issn', dict([ (t("./@type", issn), t("./text()", issn))
                                   for issn in x("//ss:issn") ])),
                    ('eissn', t(".//ss:eissn/text()")),
                    ('isbn', [ t("./text()", isbn) for isbn in x("//ss:isbn") ])
                ),
                'linkGroups' : [ {
                    'type' : t("./@type", group),
                    'holdingData' : m({
                            'providerId' : t(".//ss:providerId/text()", group),
                            'providerName' : t(".//ss:providerName/text()", group),
                            'databaseId' : t(".//ss:databaseId/text()", group),
                            'databaseName' : t(".//ss:databaseName/text()", group),
                        },
                        # output normalizedData/startDate instead of startDate,
                        # assuming that 'startDate' is redundant
                        ('startDate' , t(".//ss:normalizedData/ss:startDate/text()", group)),
                        ('endDate' , t(".//ss:normalizedData/ss:endDate/text()", group))),
                    # assumes at most one URL per type
                    'url' : dict([ (t("./@type", url), t("./text()", url))
                                   for url in x("./ss:url", group) ])
                } for group in x("//ss:linkGroups/ss:linkGroup")]
            } for result in x("//ss:result") ] },
            # optional
            ('diagnostics',
                [ m({ 'uri' : t("./sd:uri/text()", diag) },
                    ('details', t("./sd:details/text()", diag)),
                    ('message', t("./sd:message/text()", diag))
                ) for diag in x("//sd:diagnostic")]
            )
            # TBD derivedQueryData
        )

    # end class Link360JSON


class Resolved(object):
    """
    Object for handling resolved Sersol queries.
    """
    def __init__(self, data):
        self.data = data;                                           assert type(self.data) == dict, type(self.data)
        self.query = data['echoedQuery']['queryString'];            assert type(self.query) == str, type(self.query)
        self.library = data['echoedQuery']['library']['name'];      assert type(self.library) == str, type(self.library)
        self.query_dict = parse_qs(self.query);            assert type(self.query_dict) == dict, type(self.query_dict)
        error = self.data.get('diagnostics', None);                 assert type(error) == str or error is None, type(error)
        if error:
            msg = ' '.join([e.get('message') for e in error if e])
            raise Link360Exception(msg)
        #Shortcut to first returned citation and link group
        self.citation = data['results'][0]['citation'];             assert type(self.citation) == dict, type(self.citation)
        self.link_groups = data['results'][0]['linkGroups'];        assert type(self.link_groups) == list, type(self.link_groups)
        self.format = data['results'][0]['format'];                 assert type(self.format) == str, type(self.format)

    # @property
    # def openurl(self):
    #     return urllib.urlencode(self.openurl_pairs(), doseq=True)

    @property
    def openurl(self):
        logger.debug( 'starting' )
        tuple_pairs = self.openurl_pairs()
        assert type( tuple_pairs ) == list, type( tuple_pairs )
        assert type( tuple_pairs[0] ) == tuple, type( tuple_pairs[0] )
        logger.debug( 'tuple_pairs, ```%s```' % pprint.pformat(tuple_pairs) )
        ## create list of utf-8 tuples
        utf8_tpl_lst = []
        for tpl in tuple_pairs:
            key, val = tpl[0], tpl[1]
            key8 = key.encode( 'utf-8' )
            if type(val) == str:
                val8 = val.encode( 'utf-8' )
                utf8_tpl_lst.append( (key8, val8) )
            elif type(val) == list:
                val8_lst = []
                for element in val:
                    val8_lst.append( element.encode('utf-8') )
                utf8_tpl_lst.append( (key8, val8_lst) )
        ourl = urllib.urlencode( utf8_tpl_lst, doseq=True )
        ourl = ourl.decode( 'utf-8' )
        assert type( ourl ) == str
        logger.debug( 'ourl, ```%s```' % ourl )
        return ourl

    @property
    def oclc_number(self):
        """
        Parse the original query string and retain certain key, values.
        Primarily meant for storing the worldcat accession number passed on
        by Worldcat.org/FirstSearch
        """
        reg = re.compile('\d+')
        dat = self.query_dict.get('rfe_dat', None)
        if dat:
            #get the first one because dat is a list
            match = reg.search(dat[0])
            if match:
                return match.group()
        return

    # def _retain_ourl_params(self):
    #     """
    #     Parse the original query string and retain certain key, values.
    #     Primarily meant for storing the worldcat accession number passed on
    #     by http://worldcat.org or FirstSearch.

    #     This could be also helpful for retaining any other metadata that won't
    #     be returned from the 360Link API.
    #     """
    #     retain = ['rfe_dat', 'rfr_id', 'sid']
    #     parsed = urlparse.parse_qs(self.query); assert type(parsed) == dict
    #     logger.debug( 'parsed, ```%s```' % pprint.pformat(parsed) )
    #     out = []
    #     for key in retain:
    #         val = parsed.get(key, None)
    #         assert type(val) == unicode, type(val)
    #         if val:
    #             out.append((key, val))
    #     return out

    def _retain_ourl_params(self):
        """
        Parse the original query string and retain certain key, values.
        Primarily meant for storing the worldcat accession number passed on
        by http://worldcat.org or FirstSearch.

        This could be also helpful for retaining any other metadata that won't
        be returned from the 360Link API.
        """
        retain = ['rfe_dat', 'rfr_id', 'sid']
        assert type(self.query) == str
        logger.debug( 'self.query, ```%s```' % self.query )
        query8 = self.query.encode( 'utf-8' )
        logger.debug( 'query8, ```%s```' % query8 )
        parsed = parse_qs( query8 ); assert type(parsed) == dict
        logger.debug( 'parsed, ```%s```' % pprint.pformat(parsed) )
        out = []
        for key in retain:
            assert type(key) == str, type(key)
            key = key.decode( 'utf-8' )
            val = parsed.get( key, None )
            logger.debug( 'initial val, ```%s```' % pprint.pformat(val) )
            assert type(val) == str or val is None or type(val) == list, type(val)
            if val:
                if type(val) == str:
                    new_val = val.decode( 'utf-8' )
                elif type(val) == list:
                    new_val = []
                    for element8 in val:
                        new_val.append( element8.decode('utf-8') )
                out.append((key, new_val))
        logger.debug( 'out, ```%s```' % out )
        return out

    # def openurl_pairs(self):
    #     """
    #     Create a default OpenURL from the given citation that can be passed
    #     on to other systems for querying.

    #     Subclass this to handle needs for specific system.

    #     See http://ocoins.info/cobg.html for implementation guidelines.
    #     """
    #     query = urlparse.parse_qs(self.query)
    #     format = self.format
    #     #Pop invalid rft_id from OCLC
    #     try:

    #         if query['rft_id'][0].startswith('info:oclcnum'):
    #             del query['rft_id']
    #     except KeyError:
    #         pass
    #     #Massage the citation into an OpenURL
    #     #Using a list of tuples here to account for the possiblity of repeating values.
    #     out = []
    #     for k, v in self.citation.items():
    #         #Handle issns differently.  They are a dict in the 360LinkJSON response.
    #         if k == 'issn':
    #             issn_dict = self.citation[k]
    #             if isinstance(issn_dict, dict):
    #                 issn = issn_dict.get('print', None)
    #             else:
    #                 issn = issn_dict
    #             if issn:
    #                 out.append(('rft.issn', issn))
    #             continue
    #         #Handle remaining keys.
    #         try:
    #             k = SERSOL_MAP[format][k]
    #         except KeyError:
    #             pass
    #         #handle ids separately
    #         if (k == 'doi'):
    #             out.append(('rft_id', 'info:doi/%s' % v))
    #         elif (k == 'pmid'):
    #             #We will append a plain pmid for systems that will resolve that.
    #             out.append(('pmid', v))
    #             out.append(('rft_id', 'info:pmid/%s' % v))
    #         else:
    #             out.append(('rft.%s' % k, v))
    #     #versioning
    #     out.append(('url_ver', 'Z39.88-2004'))
    #     out.append(('version', '1.0'))
    #     #handle formats
    #     if format == 'book':
    #         out.append(('rft_val_fmt', 'info:ofi/fmt:kev:mtx:book'))
    #         out.append(('rft.genre', 'book'))
    #     #for now will treat all non-books as journals
    #     else:
    #         out.append(('rft_val_fmt', 'info:ofi/fmt:kev:mtx:journal'))
    #         out.append(('rft.genre', 'article'))
    #     #Get the special keys.
    #     retained_values = self._retain_ourl_params()
    #     out += retained_values
    #     return out

    def openurl_pairs(self):
        """
        Create a default OpenURL from the given citation that can be passed
        on to other systems for querying.

        Subclass this to handle needs for specific system.

        See http://ocoins.info/cobg.html for implementation guidelines.
        """
        query = parse_qs(self.query)  # creates a dct
        format = self.format
        #Pop invalid rft_id from OCLC
        try:
            if query['rft_id'][0].startswith('info:oclcnum'):
                del query['rft_id']
        except KeyError:
            pass
        #Massage the citation into an OpenURL
        #Using a list of tuples here to account for the possiblity of repeating values.
        out = []
        for k, v in self.citation.items():
            assert type(k) == str, type(k)
            #Handle issns differently.  They are a dict in the 360LinkJSON response.
            if k == 'issn':
                issn_dict = self.citation[k]
                if isinstance(issn_dict, dict):
                    issn = issn_dict.get('print', None)
                else:
                    issn = issn_dict
                assert type(issn) == str or type(issn) == dict or issn is None
                if issn:
                    out.append(('rft.issn', issn))
                continue
            #Handle remaining keys.
            try:
                k = SERSOL_MAP[format][k]
                assert type(k) == str
            except KeyError:
                pass
            #handle ids separately
            if (k == 'doi'):
                assert type(v) == str
                out.append(('rft_id', 'info:doi/%s' % v))
            elif (k == 'pmid'):
                assert type(v) == str
                #We will append a plain pmid for systems that will resolve that.
                out.append(('pmid', v))
                out.append(('rft_id', 'info:pmid/%s' % v))
            else:
                out.append(('rft.%s' % k, v))
        #versioning
        out.append(('url_ver', 'Z39.88-2004'))
        out.append(('version', '1.0'))
        #handle formats
        if format == 'book':
            out.append(('rft_val_fmt', 'info:ofi/fmt:kev:mtx:book'))
            out.append(('rft.genre', 'book'))
        #for now will treat all non-books as journals
        else:
            out.append(('rft_val_fmt', 'info:ofi/fmt:kev:mtx:journal'))
            out.append(('rft.genre', 'article'))
        #Get the special keys.
        retained_values = self._retain_ourl_params()
        out += retained_values
        return out

    # end class Resolved
