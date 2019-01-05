'''
Input parameters to scrape company financial accounting reports to the SEC
'''

# 1. Specify which companies
# Corporate identifier; note that these strings need to be all lowercase
cik_map = {'aig': '0000005272', 'axa': '0001333986', 'chubb': '0000896159',
           'cna': '0000021175', 'hartford': '0000874766',
           'metlife': '0001099219', 'new york life': '0001099219',
           'progressive': '0000080661', 'travelers': '0000086312'}


cik_map_short = {'aig': '0000005272'}  #, 'chubb': '0000896159'}

# Following companies are non-US based and so likely require a different data
# retrieval procedure
# Allianz, AXA (non-US subsidiaries), Munich Re, QBE, RSA, Zurich
# Chubb refers to Hartford Financial Services as HIG

# 2. Specify the type of report; possible values include:
'''
Prospectus		        424		Provides general information about the company	
Annual report		    10-K  	Annual statement of a company's finances	
Quarterly report		10-Q	Quarterly statement of a company's finances	
Annual proxy statement	14-K	Information about company owners	
Current events report	8-K		Notification of important event	
Sale of securities		144		Notification of significant sale of stock	
Beneficial ownership 	13-D	Identifies prominent owner (>5%) of company'''

# 3. Specify a prior-to date in YYYYMMDD format, meaning obtain all reports
# prior to that date
# 4. Count: Specify how many reports of the type specified above prior to
# dateb; does not work as expected; None is okay, as it will be ignored and
# all available reports will be listed on the search page
# 5. By default, EDGAR provides all of reports available for a company,
#  regardless
# of the source; equivalent to setting `owner` to 'include'.
# If only, EDGAR will only provide reports related to director or officer ownership

args = {'type': '10-Q', 'dateb': '20190101', 'count': 100, 'owner': 'only'}
# possibilities for 'owner' are include (default), exclude, or only

# 6. List the financial accounting metrics to retrieve
financials = ['AssetsCurrent', 'DirectOperatingCosts', 'EarningsPerShareBasic',
              'InterestAndDebtExpense', 'IntangibleAssetsCurrent',
              'NetIncomeLoss', 'NonInterestExpense', 'OperatingExpenses',
              'Revenues', 'SharesOutstanding', 'StockholdersEquity',
              'liabilitiesandstockholdersequity']

financials_short = ['AssetsCurrent', 'NetIncomeLoss']

ancillaries = ['entityregistrantname', 'entitycentralindexkey',
               'documentfiscalperiodfocus', 'documentperiodenddate',
               'documenttype', 'exchangesymbol', 'amendmentFlag']


# In development; metrics to calculate
efs = ['price_to_book']

# cash flow operations, investment, and financing

# Profitability
# ROA (NI / average total assets)
# ROE (NI / average SE); typically 5% to 18%, with goal at least 12%
# Net investment yield (net investment income / average invested assets) (4
# to 12%)

# Ceded premium ratio = ceded premium / gross premium written
# Retention ratio = 1 - CPR
# Net premiums written = Gross premiums(retention ratio)


# Pricing influenced by interest rates, while demand for insurance could be
# normalized by GDP


# Underwriting performance

# Degree of leverage and/or pricing power
# Net premiums written to surplus -- how well has an insurer leveraged its
# capital to write business (capacity utilization)
# Net written premiums / policyholder's surplus, where PS = SE for public
# companies (term exists for mutuals); regulators permit 2-to-1; typically
# 0.2 to 0.7 due to inability to charge higher premiums

# Combined ratio = loss ratio + expense ratio + dividend ratio
# Loss ratio = (losses + LAE) / earned premiums (60% to 80%)
# Expense ratio = acquisition & operating expenses / written premiums (25% to 35%)
# Dividend ratio = Policyholder dividends / earned premiums (1.0% to 2.0%)
#

# Liquidity: ability to convert assets into cash to pay claims & other expenses

