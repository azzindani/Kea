
import pandas_datareader.data as web
import pandas_datareader.famafrench as ff

from shared.logging import get_logger
import pandas as pd
import datetime

logger = get_logger(__name__)

async def get_fama_french_data(dataset_name: str = None, start_date: str = None, end_date: str = None) -> str:
    """
    Get Fama-French Data.
    dataset_name: Code (e.g., 'F-F_Research_Data_Factors').
    """
    name = dataset_name
    
    if not start_date:
        # Default to last 5 years
        start = datetime.datetime.now() - datetime.timedelta(days=365*5)
    else:
        start = start_date
        
    try:
        # returns dict of DataFrames (e.g. {0: Monthly, 1: Annual})
        # We usually want the first one (highest freq)
        # Monkeypatch pandas.read_csv temporarily to strip 'date_parser' (removed in Pandas 2.0)
        # pandas_datareader hasn't fully updated yet
        _original_read_csv = pd.read_csv
        
        def _patched_read_csv(*args, **kwargs):
            if 'date_parser' in kwargs:
                kwargs.pop('date_parser')
            return _original_read_csv(*args, **kwargs)
            
        pd.read_csv = _patched_read_csv
        
        # Also patch the module-level import if it exists (common in PDR)
        _original_ff_read_csv = getattr(ff, 'read_csv', None)
        if _original_ff_read_csv:
            setattr(ff, 'read_csv', _patched_read_csv)
            
        try:
            ds = web.DataReader(name, "famafrench", start=start, end=end_date)
        finally:
            pd.read_csv = _original_read_csv
            if _original_ff_read_csv:
                setattr(ff, 'read_csv', _original_ff_read_csv)
        
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
