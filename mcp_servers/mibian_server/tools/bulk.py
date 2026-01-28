
from mcp_servers.mibian_server.tools.core import MibianCore, df_to_json
import pandas as pd
import json


async def price_option_chain(data: list[dict]) -> str:
    """
    Bulk Price a Chain of Options.
    Args:
        data: List of dicts. Each dict must have:
              - underlying (float)
              - strike (float)
              - interest (float)
              - days (float)
              - volatility (float) [Required for pricing]
              - model (str) [Optional, default 'BS']
    """
    try:
        input_data = data # arguments.get("data", [])
        if isinstance(input_data, str): input_data = json.loads(input_data)
        
        results = []
        for item in input_data:
            try:
                model = item.get("model", "BS")
                args = [item['underlying'], item['strike'], item['interest'], item['days']]
                vol = item.get('volatility')
                
                # Metadata to keep in result
                res = item.copy()
                
                # Calculate
                calc = MibianCore.calculate(model, args, volatility=vol)
                res.update(calc)
                results.append(res)
            except Exception as e:
                item['error'] = str(e)
                results.append(item)
                
        df = pd.DataFrame(results)
        return df_to_json(df, "Option Chain Pricing")
        
    except Exception as e:
        return f"Error: {str(e)}"



async def calculate_iv_surface(data: list[dict]) -> str:
    """
    Bulk Calculate Implied Volatility Surface.
    Args:
        data: List of dicts. Must have:
              - underlying, strike, interest, days
              - call_price OR put_price (floats)
              - model (default BS)
    """
    try:
        input_data = data # arguments.get("data", [])
        if isinstance(input_data, str): input_data = json.loads(input_data)
        
        results = []
        for item in input_data:
            try:
                model = item.get("model", "BS")
                args = [item['underlying'], item['strike'], item['interest'], item['days']]
                
                # Check for price
                cp = item.get('call_price')
                pp = item.get('put_price')
                
                res = item.copy()
                
                # Mibian calculates IV if price provided
                calc = MibianCore.calculate(model, args, callPrice=cp, putPrice=pp)
                
                # Extract specifically IV
                if 'implied_volatility' in calc:
                    res['implied_volatility'] = calc['implied_volatility']
                else:
                    res['error'] = "Could not calc IV"
                
                results.append(res)
            except Exception as e:
                item['error'] = str(e)
                results.append(item)
                
        df = pd.DataFrame(results)
        return df_to_json(df, "IV Surface")
        
    except Exception as e:
        return f"Error: {str(e)}"

