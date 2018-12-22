# Scrape & structure financial accounting data from the SEC

### (incomplete work in progress)

Starting circa 2009, the U.S. Securities & Exchange Commision required publicly 
traded firms to provide financial results in a standardized, machine-readable, format. Using
 open-source Python libraries, it is possible to automatically extract 
 financial accounting data from such filings and feed them into customized analytical models & reports.
 
This document explains how the code in this repo works, with particular 
attention to structural design choices that should help you adapt the code to
 your specific needs.
 
## 1. Create a URL that conforms to the SEC's expectation
### Function: `sec_search_html`

Confined to a company, report type (10-K or 10-Q or 5-, etc.), latest date, 
and report quantity

## 2. Navigate that URL & extract links to each filing
### Function(s): `get_doc_link`

## 3. Navigate to the page of an individual filing & get the link to the XBRL-formatted report
### Function(s): `get_tags`


## 4. Scrape the [XBRL](https://xbrl.us/) report for financial metrics and tabulate
### Function(s): `metrics`

The raw data are contained in an XML document, with copious amounts of HTML 
tags, formatting, and other code we do not need.  Using Python & a decent code 
editor, we can view a cleaned up version of this raw data using 
[BeautifulSoup's](https://www.crummy.com/software/BeautifulSoup/) `.prettify()` method.

    # Obtain XBRL text from document
    xbrl = requests.get(xbrl_link)
    xbrl_str = xbrl.text  # --> py-xbrl package
    soup_xbrl = BeautifulSoup(xbrl_str, 'lxml')

    with open(self.path, 'w') as fp:
        fp.write(soup_xbrl.prettify())

Search through this ~10k-line file to check and troubleshoot your parsing.

`us-gaap` tags financial metrics in the document. It is a prefix for a much 
longer (more specific) tag, as indicated by the string following the colon. 
For instance, a firm's net income is tagged as `us-gaap:netincomeloss`. Other
 tag suffixes are listed [here](http://www.xbrlsite.com/LinkedData/BrowseObjectsByType_HTML.aspx?Type=%5BConcept%5D&Submit=Submit).
Even at this level of granularity, there can be multiple instances of a 
financial metric, such as the net income of a subsidiary or in the prior-year 
quarter. We can parse the first instance from the doc using the `find()` 
method, but the code in its current form obtains all instances, using 
`find_all()`. To distinguish these replicates, we concurrently record the 
financial metrics’ ‘context’, which include at least four attributes:

* `contextref`: a string containing dates & legal entity values that need to be
 further parsed; two examples:
 
    `FROM_Jul01_2018_TO_Sep30_2018_Entity_0000005272_dei_LegalEntityAxis_srt_ParentCompanyMember`

    `AS_OF_Dec31_2017_Entity_0000005272`
    
As shown in these two examples, the values of `contextref` vary depending on the
metric. If `contextref` always started with `FROM_` followed by a date,
 we could use `str.split()` method in combination with a slice to isolate 
 the dates. But since we want this tool to be able to retrieve more than one 
 metric at a time, it needs to automatically handle variations in `contextref`
 and other attributes, not just those that start with `FROM_`.  Regular 
 expressions provide the needed level of flexibility, as illustrated in the 
 code.

* `unitref`: the monetary currency in which the metric was reported

* 'decimals': the extent of rounding, where a negative six would indicate 
rounding to the nearest million. The code scales the raw metric values 
accordingly; i.e., 17765000000 becomes 17,765 million

* `id`: appears to be a report-tracking ID of little use



## References
[Accessing financial reports in the EDGAR database](https://www.codeproject.com/Articles/1227268/Accessing-Financial-Reports-in-the-EDGAR-Database)

[Parsing XBRL with Python](https://www.codeproject.com/Articles/1227765/Parsing-XBRL-with-Python)

[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)