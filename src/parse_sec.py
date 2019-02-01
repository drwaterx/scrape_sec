"""
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

"""

from pathlib import Path
import regex

try:
    import requests
except ImportError:
    print('Using urllib instead of requests')

import requests  # substitute for urllib
from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
import pandas as pd
import numpy as np
# import itertools
# from xbrl import XBRLParser, GAAP, GAAPSerializer, DEISerializer


class ScrapeSEC:

    def __init__(self, ciks, args, ym=None, arch=False, ancil=None,
                 path=Path.home()/'sec_temp.tree'):
        """

        Args:
            ciks (dict): list of company central index keys
            args (dict): dictionary of parameters
            path: directory in which to save (interim) outputs
            ym (str): year & month of the reporting period of interest
            ancil (list): ancillary data to add to the output data set
        """
        self.ciks = ciks
        self.args = args
        self.yearmonth = ym
        self.parser_ = 'html.parser'
        self.path = path
        self.archive = arch
        self.ancillaries = ancil

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

    def get_doc_link(self, cik):
        """
        Scrapes the tabular search results for a firm & filing type until it
        finds the selected year

        Returns:
            Hyperlink to one SEC filing

        """
        # Get the HTML code of the SEC's search results page
        edgar_str = ScrapeSEC.sec_search_html(self, cik)

        # Instantiate the HTML parser
        bs = BeautifulSoup(edgar_str, self.parser_)

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
            # print(part)
            # print('-' * 78)
            cells = part.find_all('td')

            # Some cells won't have expected content
            if len(cells) > 3:

                # Further select by date
                # 4th row of section contains the report filing date
                # ! use regex?
                # if str(2018) in cells[3].text:  # self.yearmonth

                # Penultimate instance contains the URL & date
                url_suffix = cells[1].a['href']
                date = cells[-2].text[0:7]  # yyyy-mm portion

                # Attempt to replace hard-coded slice with a regex
                # pat = regex.compile(r'\d{4}-\d{2}-\d{2}')
                # date = pat.find(cells[0].find(pat)

                # Store filing date & corresponding hyperlink in a dictionary
                doc_links[date] = ('https://www.sec.gov' + url_suffix)

        print(f'Report dates\n--------------------------\n{doc_links.keys()}')

        return doc_links

    def get_tags(self, cik):
        """
        Obtain HTML for EDGAR filing page by first obtaining the doc link from
        the EDGAR search page

        Args:
            parser_:

        Returns:

        """
        # get_tags calls get_doc_link, which calls sec_search_html
        # get_doc_link returns a dict of URLs by date YYYY-MM-DD; select which
        doc_resp = requests.get(ScrapeSEC.get_doc_link(self,
                                                       cik)[self.yearmonth])
        # doc_resp = requests.get(doc_link)  # test
        doc_str = doc_resp.text

        # Find the row of the table containing the XBRL link
        bs = BeautifulSoup(doc_str, self.parser_)

        # Find table <table class="tableFile" summary="Data Files">
        # Page should also have a table with summary='Document Format Files'
        table_tag = bs.find('table', class_='tableFile', summary='Data Files')
        parts = table_tag.find_all('tr')

        # Each 'part' has a penultimate instance of <td> with a file name
        # ending in a three-character extension: INS, SCH, CAL, DEF, LAB,
        # PRE; INS is the main XML we want; others are unknown

        for part in parts:
            # print(part)

            cells = part.find_all('td')

            # Fetch link to XML file containing financial data
            # Desired hyperlink suffix appears multiple times; IF statements
            # help locate the correct instance (use regex?)
            if len(cells) > 3:
                if 'INS' in cells[3].text:
                    xbrl_link = 'https://www.sec.gov' + cells[2].a['href']

        try:
            # Obtain XBRL text; optionally save for python-xbrl
            xbrl = requests.get(xbrl_link)
            xbrl_str = xbrl.text  # --> py-xbrl package
            soup_xbrl = BeautifulSoup(xbrl_str, 'lxml')

            # Serialize with added whitespace for visual clarity
            if self.archive:
                with open(self.path, 'w') as fp:
                    fp.write(soup_xbrl.prettify())
        except requests.exceptions.MissingSchema:
            print('Did not retrieve a valid URL to XBRL from the filing\'s '
                  'main web page')
            soup_xbrl = None

        # Return list of XBRL tags & associated content (attributes & text)
        return soup_xbrl

    def metrics(self, financials):

        # Iterates over firms for one date
        for cik in self.ciks:
            soup_xbrl = ScrapeSEC.get_tags(self, cik)

            # Create empty list; each item will be one firm's metrics
            dfs = []

            # Iterates over metrics for one firm & date
            for met in [x.lower() for x in financials]:

                idx = 0  # row indexer

                # Define regular expression: Any tag starting with...
                pat = regex.compile('^us-gaap:' + met)

                try:
                    # Create an empty DataFrame with a column for each attribute
                    # .attrs is a Beautiful Soup method to obtain a dict of
                    # the content tagged per regex pattern
                    df = pd.DataFrame(columns=list(soup_xbrl.find(pat).attrs.
                                                   keys()) +
                                              ['metric_name', 'metric_value'])

                    # Extract all instances of one metric & the contextual
                    # info needed to distinguish them
                    for tag in soup_xbrl.find_all(pat):

                        # Retrieve context of metric (tag attributes)
                        # .attrs is a dictionary
                        # 'contextref' contains values that need to be parsed
                        # 'unittref' usually USD
                        # 'decimals' e.g., -6, or rounded to nearest million
                        # Place list of attribute values in row idx of the
                        # DataFrame
                        df.loc[idx] = list(tag.attrs.values()) + [np.nan, np.nan]

                        # If decimals is positive, metric is pre-normalized
                        # (e.g., EPS), so don't scale; but if 'decimals' is
                        # negative, value has been rounded, so scale
                        # accordingly
                        if float(df[idx:idx+1].decimals) < 0:
                            scale = abs(float(df[idx:idx+1].decimals))
                        else:
                            scale = 1.

                        # Add scaled name & value
                        df.loc[idx, 'metric_name'] = tag.name
                        df.loc[idx, 'metric_value'] = float(tag.text) / scale

                        idx += 1

                    # Append DataFrame to a list
                    dfs.append(df)

                except AttributeError:
                    print(f'{met} is unavailable')

            # Concatenate the DataFrames & reset the index
            dfm = pd.concat(dfs)
            dfm.reset_index(inplace=True, drop=True)

            # Deprecated: DataFrame from flattened list of lists of tuples
            # df = pd.DataFrame(sorted(itertools.chain(*groups)), columns=[
            #     'metric_name', 'context', 'metric_value', 'units'])

            # -----REGEX SANDBOX------------------------------------------------
            # pat_ctxt = regex.compile('(AS_OF_)|(FROM_)|(_TO_)|(_Entity_)')
            # pat_ctxt = regex.compile('([A-Z]{1}[a-z]{2}\d{2}_\d{4})|('
            #                          'Entity_\d*)|(dei_LegalEntityAxis_)')
            # pat_test.findall(pat_ctxt)
            #
            # ------------------------------------------------------------------

            # Define a pattern to find MmmDD_YYYY dates
            pat_date = regex.compile('([A-Z]{1}[a-z]{2}\d{2}_\d{4})')

            # Extract the dates from contextref & place into two columns; a
            # NaN or None will be placed in the 2nd column as appropriate
            # The DataFrame constructor and .values.tolist() handles the list
            # provided by regex's findall()
            dfm[['t0', 't1']] = pd.DataFrame(
                dfm.contextref.apply(lambda x: pat_date.findall(x)).
                                     values.tolist(), index=dfm.index)

            # 1. Place a list of timestamps in one column
            # dfm.loc[:, 'timestamps'] = dfm.contextref.apply(lambda x:
            #                                                 pat_date.findall(x))
            # 2. To separate the list, extract & replace
            # dfm[['t0', 't1']] = pd.DataFrame(dfm.timestamps.values.tolist(),
            #                                  index=dfm.index)

            # Print list of tags' contexts
            for c in dfm.contextref:
                print(c)  # Entity_ followed by CIK standard length; does
                # regex have a 'give me what follows pat'?

            # Define a pattern to find the legal entity from contextref
            pat_entity = regex.compile('(srt_.*)')
            dfm.loc[:, 'entity'] = dfm.contextref.apply(lambda x:
                pat_entity.findall(x))   #[3:])

            # Add categories to the DataFrame
            for anc in self.ancillaries:
                try:
                    dfm.loc[:, anc] = soup_xbrl.find('dei:' + anc).text
                except AttributeError:
                    print(f'The attribute {anc} was not found')

            # dfm.loc[:, 'firm'] = soup_xbrl.find('dei:entityregistrantname').text
            # dfm.loc[:, 'cik'] = soup_xbrl.find('dei:entitycentralindexkey').text
            # dfm.loc[:, 'quarter'] = soup_xbrl.find('dei:documentfiscalperiodfocus').text
            # dfm.loc[:, 'date_filing'] = soup_xbrl.find('dei:documentperiodenddate').text
            # dfm.loc[:, 'filing'] = soup_xbrl.find('dei:documenttype').text
            # dfm.loc[:, 'year'] = date_filing[0:4]
            # dfm.loc[:, 'day'] = date_filing[5:7]

            dfm.metric_name = dfm.metric_name.apply(lambda x: x.strip(
                'us-gaap:'))

            # Print summary
            # firm = soup_xbrl.find('dei:entityregistrantname').text
            # print(f'{c} instances of {met} found for {firm}, {yr}-{qtr}\n')

        return dfm
