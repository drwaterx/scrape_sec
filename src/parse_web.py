'''
Programmatic retrieval of publicly traded company SEC filings from 2009 on

This code accomplishes a type of web scraping, which generally involves
gathering data from HTML-based web pages in a useful format while preserving
structure of the data

eXtensible Business Reporting Language (XBRL) is based on the
eXtensible Markup Language (XML), but uses special tags to mark financial
data. Define tags and attributes by creating a schema. Schemas are defined
with XML Schema Definition (XSD), having the suffix *.xsd. An XML document
can access the tags and attributes of a schema using a namespace declaration.
For example, the following declaration specifies that the XML document will
access the tags and attributes defined in the schema located at http://www.example.com:

xmlns:ex="http://www.example.com"

Common namespaces accessed in American reports:

1. Base XBRL Schema - Provides the overall structure of an XBRL document

The fundamental tags and attributes of XBRL are provided in the schema located at http://www.xbrl.org/2003/instance. Documents commonly access these elements through the xbrli prefix, as given in the following namespace declaration:

xlmns:xbrli="http://www.xbrl.org/2003/instance"

To understand other tags provided by the base schema, you should be familiar with the following terms:

    instance - an XBRL document whose root element is <xbrli:xbrl>
    fact - An individual detail in a report, such as $20M
    concept - The meaning associated with a fact, such as the cost of goods sold
    entity - The company or individual described by a concept
    context - A data structure that associates an entity with a concept

2. US Document and Entity Information (DEI) - Sets a document's type and
characteristics


3. US Generally Accepted Accounting Principles (GAAP) - Defines required
elements of American reports


4. Entity-specific Schema - Defines elements specific to the entity
providing the report


single document may need to access features from many different schemas

References:
    [1] https://www.codeproject.com/Articles/1227268/Accessing-Financial-Reports-in-the-EDGAR-Database
    [2] https://www.codeproject.com/Articles/1227765/Parsing-XBRL-with-Python
'''

from pathlib import Path
import regex
import itertools
import requests  # substitute for urllib
# from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from xbrl import XBRLParser, GAAP, GAAPSerializer, DEISerializer
import pandas as pd
# import datetime as dt
pd.set_option('precision', 3)
pd.set_option('display.expand_frame_repr', False)


class ScrapeSEC:

    def __init__(self, ciks={}, args={}, scale=1e6, ym=None, arch=False,
                 path=Path.home()/'sec_temp.tree'):
        """

        Args:
            ciks (list): list of company identifier keys
            args (dict): dictionary of parameters
            scale (float): scalar; typically to express financials in millions
            path: directory in which to save (interim) outputs
            ym (str): year & month of the reporting period of interest
        """
        self.ciks = ciks
        self.args = args
        self.yearmonth = ym
        self.parser_ = 'html.parser'
        self.path = path
        self.scale = scale
        self.archive = arch

    def cik2firm(self):
        """
        Looks up company name associated with its CIK

        Args:
            cik (str): CIK code of company
            ciks (dict): map of company abbreviations to CIK codes

        Returns:
            Company abbreviated name
        """
        for name, cik_ in self.ciks.items():
            if cik_ == cik:
                return name
            else:
                return '-unk-'

    def sec_search_html(self, cik):
        """
        Obtains the HTML contents of a web page whose URL conforms to the U.S.
        SEC's EDGAR site specifying a specific filing from a specific firm. The
        page contains the search results for that company & filing type,
        which are primarily hyperlinks to pages (one page per filing).

        Args:
            cik (str): company code
            args (dict): type of SEC filing (e.g., 10-K), the date-before
            parameter, and number of reports

        Returns:
            String of HTML page contents

        """

        # Obtain HTML for search page
        base_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany" \
                   "&CIK={}&type={}&dateb={}&count={}"

        # Send request to the URL and receive an HTML response
        try:
            edgar_html = requests.get(base_url.format(
                cik, self.args['type'], self.args['dateb'],
                str(self.args['count'])))
            # edgar_html = urlopen(base_url.format(cik, args['type'],
            #     args['dateb'], str(args['count'])))
        except HTTPError as e:
            print(e)
            edgar_html = None
        except URLError as e:
            print('The server could not be found')
            edgar_html = None

        # Parse the HTML to find the URL(s) of the report(s) of interest
        return edgar_html.text

    def get_doc_link(self):
        """
        Scrapes the tabular search results for a firm & filing type until it
        finds the selected year

        Returns:
            Hyperlink to one SEC filing

        """
        # Get the HTML code of the SEC's search results page
        edgar_str = ScrapeSEC.sec_search_html(self, cik)

        # Instantiate the HTML parser
        bs = BeautifulSoup(edgar_str, 'html.parser')  # self.parser

        # Find the 1st table tag with the specified class_ attribute
        # EDGAR search results page is a table
        table_tag = bs.find('table', class_='tableFile2')
        # table_tag.attrs  # view attributes of the tag

        # Table contains a multiple parts wrapped by <tr> </tr> tags,
        # differing by filing date & corresponding URL suffix
        parts = table_tag.find_all('tr')

        # Assemble all available URLs
        doc_links = {}
        for part in parts:
            print(part)
            print('----------------------------------------------')
            cells = part.find_all('td')

            # Some cells won't have expected content
            if len(cells) > 3:
                # Assuming the second instance contains the URL & date in
                # penultimate instance
                url_suffix = cells[1].a['href']
                date = cells[-2].text[0:7]  # yyyy-mm portion

                # Attempt to replace hard-coded slice with a regex
                # pat = regex.compile(r'\d{4}-\d{2}-\d{2}')
                # date = pat.find(cells[0].find(pat)

                # Store filing date & corresponding hyperlink in a dictionary
                doc_links[date] = ('https://www.sec.gov' + url_suffix)

        # Obtain one URL suffix corresponding to one filing date
        # for part in parts:
        #     print(part)
        #     print('-----------')
        #     # Between <tr> and </tr> are 5 <td> tags
        #     # Instead of if statement checking len(cells), use lambda to
        #     # restrict cells at the point of declaration
        #     cells = parts[0].find_all('td')
        #     # cells = row.find_all({'td': lambda tag: len(tag) > 3})
        #     if len(cells) > 3:  # verify <tr>'d content is as expected
        #
        #         # 4th row of section contains the report filing date
        #         # ! opportunity to use regex?
        #         if str(2018) in cells[3].text:  # self.yearmonth
        #             # Get link to report from 2nd row; instead of using
        #             # .find(), call the 'a' tag directly
        #             doc_link = 'https://www.sec.gov' + cells[1].a['href']
        #
        #     print(f"Couldn't find the link to the filing for {
        #     self.yearmonth}")

        return doc_links

    def get_tags(self):
        """
        Obtain HTML for EDGAR filing page by first obtaining the doc link from
        the EDGAR search page

        Args:
            parser_:

        Returns:

        """
        # get_tags calls get_doc_link, which calls sec_search_html
        # get_doc_link returns a dict of URLs by date YYYY-MM-DD; select which
        doc_resp = requests.get(ScrapeSEC.get_doc_link(self)[self.yearmonth])
        doc_str = doc_resp.text

        # Find the row of the table containing the XBRL link
        bs = BeautifulSoup(doc_str, 'html.parser')  # self.parser_)

        # Find table <table class="tableFile" summary="Data Files">
        # Page should also have a table with summary= 'Document Format Files'
        table_tag = bs.find('table', class_='tableFile', summary='Data Files')
        parts = table_tag.find_all('tr')

        # Each 'part' has a penultimate instance of <td> with a file name
        # ending in a three-character extension: INS, SCH, CAL, DEF, LAB,
        # PRE; INS is the main XML; don't know what the others are

        for part in parts:
            # print(part)
            # print('----------------------------------------------')
            cells = part.find_all('td')
            # pat = regex.compile(r'.*\/Archives\/edgar\/data\/\d*.*')
            # cells = part.find_all('td', {'scope': pat})

            if len(cells) > 3:
                # The suffix to the hyperlink that we want appears multiple
                # times, first in part prior to the report type
                # More robust might be a regex
                if 'INS' in cells[3].text:
                    # Fetch link to XML file containing financial data
                    xbrl_link = 'https://www.sec.gov' + cells[2].a['href']
        # Obtain XBRL text from document; this link is the one to save for
        # python-xbrl
        xbrl = requests.get(xbrl_link)
        xbrl_str = xbrl.text  # --> py-xbrl package
        soup_xbrl = BeautifulSoup(xbrl_str, 'lxml')

        if self.archive:
            with open(self.path, 'w') as fp:
                fp.write(soup_xbrl.prettify())

        # Return list of XBRL tags & associated content (attributes & text)
        return soup_xbrl

    def metrics(self, financials):

        dfs = []
        for cik in self.ciks:
            soup_xbrl = ScrapeSEC.get_tags(self, cik)

            firm = soup_xbrl.find('dei:entityregistrantname').text
            # ticker = soup_xbrl.find('dei:entityregistrantname').text
            date_filing = soup_xbrl.find('dei:documentperiodenddate').text
            yr = date_filing[0:4]
            qtr = soup_xbrl.find('dei:documentfiscalperiodfocus').text
            # day = date_filing[5:7]

            # Assemble data set for one firms, financial metrics, and times
            groups = []
            for met in [x.lower() for x in financials]:
                items = []
                # items = {}
                pat = regex.compile('^us-gaap:' + met)  # starts with...
                c = 0
                for tag in soup_xbrl.find_all(pat):  # ScrapeSEC.get_tags(self):
                    # Display name & value of the financial datum in the console
                    # print('{}: {:,}'.format(tag.name, float(tag.text)/1e6))

                    # Store data in a dictionary; data overwritten if financial
                    # recurs
                    # items[tag.name] = float(tag.text)/1e6  # self.scale
                    items.append((tag.name, float(tag.text)/1e6))  # self.scale
                    c += 1

                # Append list of tuples to a parent list
                groups.append(items)

                # Construct DataFrame from flattened list of lists of tuples
                df = pd.DataFrame(sorted(itertools.chain(*groups)), columns=[
                    'metric_name', 'metric_value'])
                df.loc[:, 'firm'] = firm
                df.loc[:, 'cik'] = cik
                # df.loc[:, 'year'] = yr
                df.loc[:, 'quarter'] = qtr
                df.loc[:, 'date_filing'] = date_filing

                # Print summary
                print(f'{c} instances of {met} found for {firm}, {yr}-{qtr}\n')

            dfs.append(df)

        return pd.concat(dfs)

# ------------------------------------------------------------------------------
# Main
# Note that these strings need to be all lowercase
cik_map = {'aig': '0000005272', 'axa': '0001333986', 'chubb': '0000896159',
           'cna': '0000021175', 'hartford': '0000874766',
           'metlife': '0001099219', 'new york life': '0001099219',
           'progressive': ' 0000080661', 'travelers': '0000086312'}

cik_map = {'aig': '0000005272'}  #, 'chubb': '0000896159'}

# Following companies are non-US based and so likely require a different data
# retrieval procedure
# Allianz, AXA (non-US subsidiaries), Munich Re, QBE, RSA, Zurich
# Chubb refers to Hartford Financial Services as HIG

# Access page
cik = '0000005272'  # corporation's identifier

# (a) Specify the type of report; possible values include:
'''
Prospectus		        424		Provides general information about the company	
Annual report		    10-K  	Annual statement of a company's finances	
Quarterly report		10-Q	Quarterly statement of a company's finances	
Annual proxy statement	14-K	Information about company owners	
Current events report	8-K		Notification of important event	
Sale of securities		144		Notification of significant sale of stock	
Beneficial ownership 	13-D	Identifies prominent owner (>5%) of company'''
# (b) Specify a prior-to date in YYYYMMDD format, meaning obtain all reports
# prior to that date
# (c) Count: Specify how many reports of the type specified above prior to
# dateb; does not work as expected; None is okay, as it will be ignored and
# all available reports will be listed on the search page
# (d) By default, EDGAR provides all of reports available for a company,
#  regardless
# of the source; equivalent to setting `owner` to 'include'.
# If only, EDGAR will only provide reports related to director or officer ownership

args = {'type': '10-Q', 'dateb': '20190101', 'count': 100, 'owner': 'only'}
# include (default), exclude, or only

financials = ['AssetsCurrent', 'DirectOperatingCosts', 'EarningsPerShareBasic',
           'InterestAndDebtExpense', 'IntangibleAssetsCurrent',
           'NetIncomeLoss', 'NonInterestExpense', 'OperatingExpenses',
           'Revenues', 'SharesOutstanding', 'StockholdersEquity',
              'liabilitiesandstockholdersequity']

financials = ['liabilitiesandstockholdersequity', 'NetIncomeLoss']

# Instantiate the scraper
iScrapeSEC = ScrapeSEC(cik, cik_map, args, 2018)

data_firms = []
for cik in cik_map.values():
    data_firm, periods, tickers = metrics(cik, args, 2018, financials)
    try:
        data_firms.append(data_firm)
    except TypeError:
        print(f'No metrics were retrieved for {cik2firm(cik, cik_map)}')

data = pd.concat(data_firms)

# ... engineer additional data

# ------------------------------------------------------------------------------
# Use of python-xbrl
xbrl_parser = XBRLParser(precision=0)

# Parse an incoming XBRL file
xbrl = xbrl_parser.parse(xbrl_str)
# xbrl = xbrl_parser.parse(Path.home()/'audit'/'data'/'sec'/'aig-20180331.xml')

# Parse just the GAAP data from the xbrl object
gaap_obj = xbrl_parser.parseGAAP(xbrl, doc_date="20180331", context="current",
                                 ignore_errors=0)

# Serialize the GAAP data
serializer = GAAPSerializer()
result = serializer.dump(gaap_obj)

# Print out the serialized GAAP data
print(result)  # .data

# Parse just the DEI data from the xbrl object
dei_obj = xbrl_parser.parseDEI(xbrl)

# Serialize the DEI data
serializer = DEISerializer()
result2 = serializer.dump(dei_obj)

# Print out the serialized DEI data
print(result2)

# Parse just the Custom data from the xbrl object
custom_obj = xbrl_parser.parseCustom(xbrl)

# Print out the Custom data as an array of tuples
print(custom_obj())


def get_cik(ticker):
  ''' this function uses yahoo to translate a ticker into a CIK '''
  url = "http://finance.yahoo.com/q/sec?s=%s+SEC+Filings" % (ticker)
  return int(regex.findall('=[0-9]*', str(regex.findall('cik=[0-9]*',
             urllib2.urlopen(url).read())[0]))[0][1:])


# ------------------------------------------------------------------------------
'''
Web scraping and parsing with Beautiful Soup & Python

1. Create a an object of the HTML source code of an web page
2. Convert the source into a Beautiful Soup object, specifying the 'lxml' parser, which lets us interact with, such as applying attributes like .title.name, .title.text, .p (1st paragraph element),

.find_all('p') all paragraph
'''

# print text between all pairs of paragraph tags
for paragraph in soup.find_all('p'):
    print(paragraph.text)

# Get all text, including that between span, and other tags
print(soup.get_text())

# Get URLs
for url in soup.find_all('a'):  # a = all
    print(url.get('href'))

# Get specific set of URLs
# Create a new soup object
nav = soup.nav  # navigation bar on a web page
for url in nav.find_all('a'):
    print(url.get('href'))

for div in soup.find_all('div', class_='body'):
    print(div.text)

'''
# Scraping tables
Various tags
table tag <table style=...>
table row tag <tr>
table header <th>
table data <td>
'''
table = soup.table  # alternatively table = soup.find('table')
table_rows = table.find_all('tr')  # Find all table rows

for tr in table_rows:
    td = tr.find_all('td')
    row = [i.text for i in td]
    print(row)  # outputs a list of strings

# With pandas
# Tries to parse HTML
dfs = pd.read_html('http://www.xbrlsite.com/LinkedData/BrowseObjectsByType_HTML.aspx?Type=%5BConcept%5D&Submit=Submit')  # put URL
for df in dfs:
    print(df)
    list_of_lists = df.values.to_list()

# XML scraping
soup = bs.BeautifulSoup(sauce, 'xml')

for url in soup.find_all('loc'):
    print(url.text)

# Libraries
Scrapy

'''
# XML Path Language
XPath is a way of locating info in HTML or XML documents by identifying and navigating nodes in an XML doc
untangle is a library returns a Python object mirroring the nodes and attributes in the structure of an XML document
xmltodict is another simpler library that allows you to access elements in the Python object generated like a dictionary: doc['mydoc']['@xx']

On Github:
pystock-crawler
py-edgar
'''
