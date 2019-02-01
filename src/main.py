from pathlib import Path
from src.params import *
from src.parse_sec import ScrapeSEC

import pandas as pd
pd.set_option('precision', 3)
pd.set_option('display.expand_frame_repr', False)

def main(cik_map, args, path=Path.home(), fname='sec_report_temp.xlsx'):
    # Instantiate the scraper
    iScrapeSEC = ScrapeSEC(cik_map_short.values(), args, ym='2018-11',
                           ancil=ancillaries)

    df = iScrapeSEC.metrics(financials=financials_short)

    df.to_excel(path / fname)

if  __name__ == '__main__':
    main(cik_map, args_xbrl)
