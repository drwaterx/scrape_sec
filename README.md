# Scrape & structure financial accounting data from the SEC

#### N.B. this is a work in progress
This code produces a tidy (long-form) table of financial accounting data of 
one or more firms, filed in one or more reports.

Starting circa 2009, the U.S. Securities & Exchange Commission required 
publicly traded firms to report financial results in a standardized, 
machine-readable, format. Using open-source Python libraries, it is possible to automatically extract 
 financial accounting data from such reports such that they can be fed 
 them into customized analytical models & reports.
 
Please see in-line documentation & references appended to understand how the 
code works and where design choices were made such that you can adapt the 
code to your specific needs. The code itself is contained in two modules, of which 
 `main.py` can be adapted into a Jupyter notebook, if you prefer, importing 
 the module `parse_sec` and specifications contained in `params`.
 
The code initiates with a call to the function `metrics`, which 
successively calls the functions summarized below.
 
### 1. Create a URL that conforms to the SEC's expectation
#### Function: `sec_search_html`

Confined to a company, report type (10-K or 10-Q or 5-, etc.), latest date, 
and report quantity

### 2. Navigate to that URL & extract links to each filing
#### Function: `get_doc_link`

### 3. Navigate to the page of an individual filing & get the link to the XBRL-formatted report
#### Function: `get_tags`


### 4. Scrape the [XBRL](https://xbrl.us/) report for financial metrics and tabulate
#### Function: `metrics`

The raw data are contained in an XML document, with copious amounts of HTML 
tags, formatting, and other code you likely do not need.  Using Python & a 
decent code editor, we can view a cleaned up version of this raw data using 
[BeautifulSoup's](https://www.crummy.com/software/BeautifulSoup/) `.prettify()` method.

    # Excerpt:
    # Obtain XBRL text from document
    xbrl = requests.get(xbrl_link)
    xbrl_str = xbrl.text
    soup_xbrl = BeautifulSoup(xbrl_str, 'lxml')

    with open(self.path, 'w') as fp:
        fp.write(soup_xbrl.prettify())

Search through this file to understand the XBRL-formatted data better & 
troubleshoot your parsing.

`us-gaap` tags financial metrics in the document. It is a prefix for a much 
longer (more specific) tag, as indicated by the string following the colon. 
For instance, a firm's net income is tagged as `us-gaap:netincomeloss`. Other
 tag suffixes are listed [here](http://www.xbrlsite.com/LinkedData/BrowseObjectsByType_HTML.aspx?Type=%5BConcept%5D&Submit=Submit).
There can be multiple instances of a 
financial metric, such as the net income of a subsidiary or in the prior year's 
quarter. We can parse the first instance from the doc using the `find()` 
method, but the code currently obtains all instances by using 
`find_all()`. To distinguish these replicates, we concurrently record the 
financial metrics’ _context_, which includes at least four attributes:

* `contextref`: a string containing dates,  legal entity names, and other 
information that need to be parsed; here are two examples:
 
    `FROM_Jul01_2018_TO_Sep30_2018_Entity_0000005272_dei_LegalEntityAxis_srt_ParentCompanyMember`

    `AS_OF_Dec31_2017_Entity_0000005272`
    
As shown in these two examples, the values of `contextref` vary depending on the
metric. If `contextref` always started with `FROM_` followed by a date,
 we could use panda's `str.split()` method in combination with a slice to 
 isolate the dates. But since we want this tool to be able to retrieve more than one 
 metric at a time, it needs to automatically handle variations in `contextref`,
 not just those that start with `FROM_`.  Regular 
 expressions provide the needed level of flexibility.
 
While regular expressions could be applied within the `str.split` operation of 
`pandas`, using `expand=True` to generate individual columns of the patterns 
and adjacencies, I found the results to be unwieldy. Instead, I 
created a regex for each `context` I wanted to extract, applying `regex
.findall()` as a `lambda` function to the DataFrame's `contextref` column. It
 is likely you will have to modify and/or add regular expressions to grab 
 everything you need.

* `unitref`: the monetary currency in which the metric was reported

* `decimals`: the extent of rounding, where a negative six would indicate 
rounding to the nearest million. [not working: code scales the raw metric 
values accordingly; i.e., 17765000000 becomes 17,765 (million)]

* `id`: appears to be a report-tracking ID of little use



### References
[Accessing financial reports in the EDGAR database](https://www.codeproject.com/Articles/1227268/Accessing-Financial-Reports-in-the-EDGAR-Database)

[Parsing XBRL with Python](https://www.codeproject.com/Articles/1227765/Parsing-XBRL-with-Python)

[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Mitchell, R., [_Web scraping with Python_](http://www.pythonscraping.com/) (2nd Ed.), O'Reilly, 2018