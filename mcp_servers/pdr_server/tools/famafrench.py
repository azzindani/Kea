
import pandas_datareader.data as web
import pandas_datareader.famafrench as ff
from contextlib import contextmanager

from shared.logging import get_logger
import pandas as pd
import datetime

logger = get_logger(__name__)


@contextmanager
def _patch_famafrench_read_csv():
    """Patch read_csv to handle date_parser removal in Pandas 2.0+.

    pandas_datareader still passes date_parser + parse_dates to read_csv,
    but Pandas 3.0 removed date_parser entirely. Without it, the Fama-French
    date formats (e.g. "192607") aren't parsed, leaving the index as raw
    integers and causing a TypeError when truncate() compares int vs Timestamp.

    Fix: strip both deprecated kwargs, call the original read_csv, then apply
    the date parser function manually to the index afterward.
    """
    _original_read_csv = pd.read_csv
    _original_ff_read_csv = getattr(ff, 'read_csv', None)

    def _patched_read_csv(*args, **kwargs):
        date_parser_func = kwargs.pop('date_parser', None)
        parse_dates_val = kwargs.pop('parse_dates', None)
        result = _original_read_csv(*args, **kwargs)
        
        # If we have a date parser and parse_dates was requested
        if date_parser_func and parse_dates_val is not None:
            try:
                # Apply the date parser manually
                result.index = result.index.map(lambda x: date_parser_func(str(x)))
                
                # Drop rows where index is NaT (crucial for PeriodIndex in Pandas 3.0)
                # Pandas 3.0 truncate/slicing fails if NaT is present in a PeriodIndex
                if hasattr(result.index, 'isna'):
                    result = result[~result.index.isna()]
                else:
                    result = result[result.index.notna()]
                    
            except Exception as e:
                logger.warning(f"Fama-French patch failed to parse dates: {e}")
        return result

    pd.read_csv = _patched_read_csv
    if _original_ff_read_csv:
        setattr(ff, 'read_csv', _patched_read_csv)
    try:
        yield
    finally:
        pd.read_csv = _original_read_csv
        if _original_ff_read_csv:
            setattr(ff, 'read_csv', _original_ff_read_csv)


def read_famafrench(name: str, start: object = None, end: object = None) -> dict:
    """Read Fama-French data with Pandas 3.0 compatibility."""
    # Ensure start/end are not empty strings which can cause issues in pdr
    if start == "": start = None
    if end == "": end = None
    
    with _patch_famafrench_read_csv():
        return web.DataReader(name, "famafrench", start=start, end=end)


async def get_fama_french_data(dataset_name: str = None, start_date: str = None, end_date: str = None) -> str:
    """
    Get Fama-French Data.
    dataset_name: Code (e.g., 'F-F_Research_Data_Factors').
    """
    name = dataset_name
    
    # Standardize empty strings to None
    start = start_date if start_date != "" else None
    end = end_date if end_date != "" else None

    if not start:
        # Default to last 5 years
        start = datetime.datetime.now() - datetime.timedelta(days=365*5)

    try:
        ds = read_famafrench(name, start=start, end=end)
        
        if not ds:
            return "No data found."
            
        # Format output
        # Keys are usually integers 0, 1, ... describing the tables (Monthly, Annual)
        # We'll just dump the first key's dataframe as markdown, or all of them.
        
        output = f"### Fama-French: {name}\n"
        if 'DESCR' in ds:
            output += f"**Description**: {ds['DESCR']}\n\n"
            
        for k, v in ds.items():
            if k == 'DESCR': continue
            output += f"#### Table {k}\n{v.tail(20).to_markdown()}\n\n"
            
        return output
        
    except Exception as e:
        logger.error(f"FamaFrench error {name}: {e}")
        return f"Error: {str(e)}"


# Mapping of Friendly Name -> Code
# Source: http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
FF_DATASETS = {
    # Main Factors
    "ff_factors_daily": "F-F_Research_Data_Factors_daily",
    "ff_factors_monthly": "F-F_Research_Data_Factors",
    "ff_5_factors_daily": "F-F_Research_Data_5_Factors_2x3_daily",
    "ff_5_factors_monthly": "F-F_Research_Data_5_Factors_2x3",
    "ff_momentum_daily": "F-F_Momentum_Factor_daily",
    "ff_momentum_monthly": "F-F_Momentum_Factor",
    
    # Industry Portfolios
    "ff_industry_5_daily": "5_Industry_Portfolios_daily",
    "ff_industry_10_daily": "10_Industry_Portfolios_daily",
    "ff_industry_30_daily": "30_Industry_Portfolios_daily",
    "ff_industry_48_daily": "48_Industry_Portfolios_daily",
    
    # Sorts
    "ff_portfolios_size_bm": "Portfolios_Formed_on_B-M",
    "ff_portfolios_size_op": "Portfolios_Formed_on_OP",
    "ff_portfolios_size_inv": "Portfolios_Formed_on_INV",
    "ff_portfolios_size_mom": "10_Portfolios_Prior_12_2",
    "ff_portfolios_size_bm_2x3": "6_Portfolios_2x3",
    "ff_portfolios_size_op_2x3": "6_Portfolios_ME_OP_2x3",
    "ff_portfolios_size_inv_2x3": "6_Portfolios_ME_INV_2x3",
    "ff_portfolios_size_mom_2x3": "6_Portfolios_ME_Prior_12_2",
    
    # Granular Industry
    "ff_industry_5": "5_Industry_Portfolios",
    "ff_industry_10": "10_Industry_Portfolios",
    "ff_industry_12": "12_Industry_Portfolios",
    "ff_industry_17": "17_Industry_Portfolios",
    "ff_industry_30": "30_Industry_Portfolios",
    "ff_industry_38": "38_Industry_Portfolios",
    "ff_industry_48": "48_Industry_Portfolios",
    "ff_industry_49": "49_Industry_Portfolios",
    
    # Univariates
    "ff_univ_size": "Portfolios_Formed_on_ME",
    "ff_univ_bm": "Portfolios_Formed_on_BE-ME",
    "ff_univ_op": "Portfolios_Formed_on_OP",
    "ff_univ_inv": "Portfolios_Formed_on_INV",
    "ff_univ_mom": "10_Portfolios_Prior_12_2",
    
    # Long Horizon
    "ff_long_horizon": "Portfolios_Formed_on_B-M", # Reused logic, different time
    
    # International Factors (Regions)
    "ff_developed_ex_us_3_factors": "Developed_ex_US_3_Factors",
    "ff_developed_ex_us_5_factors": "Developed_ex_US_5_Factors",
    
    # International Factors (Countries - Selected)
    "ff_uk_3_factors": "UK_3_Factors",
    "ff_france_3_factors": "France_3_Factors",
    "ff_germany_3_factors": "Germany_3_Factors",
    "ff_italy_3_factors": "Italy_3_Factors",
    "ff_canada_3_factors": "Canada_3_Factors",
    "ff_australia_3_factors": "Australia_3_Factors",
    
    # International
    "ff_developed_3_factors": "Developed_3_Factors",
    "ff_developed_5_factors": "Developed_5_Factors",
    "ff_emerging_5_factors": "Emerging_5_Factors",
    "ff_european_3_factors": "Europe_3_Factors",
    "ff_japanese_3_factors": "Japan_3_Factors",
    "ff_asiapacific_3_factors": "Asia_Pacific_ex_Japan_3_Factors",
    "ff_northamerica_3_factors": "North_America_3_Factors",
    
    # Fundamentals Sorts
    "ff_portfolios_dividend_yield": "Portfolios_Formed_on_D-P",
    "ff_portfolios_earnings_price": "Portfolios_Formed_on_E-P",
    "ff_portfolios_cashflow_price": "Portfolios_Formed_on_CF-P",
    "ff_portfolios_net_issues": "Portfolios_Formed_on_NI",
    "ff_portfolios_accruals": "Portfolios_Formed_on_AC",
    "ff_portfolios_beta": "Portfolios_Formed_on_BETA",
    "ff_portfolios_variance": "Portfolios_Formed_on_VAR",
    "ff_portfolios_residual_var": "Portfolios_Formed_on_RESVAR"
}

def get_ff_map():
    return FF_DATASETS
