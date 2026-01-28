
import mibian

import pandas as pd
import json

class MibianCore:
    @staticmethod
    def _extract_results(obj) -> dict:
        """Extract all available attributes from a Mibian object."""
        res = {}
        # Pricing & Greeks
        if hasattr(obj, 'callPrice'): res['call_price'] = obj.callPrice
        if hasattr(obj, 'putPrice'): res['put_price'] = obj.putPrice
        if hasattr(obj, 'callDelta'): res['call_delta'] = obj.callDelta
        if hasattr(obj, 'putDelta'): res['put_delta'] = obj.putDelta
        if hasattr(obj, 'callTheta'): res['call_theta'] = obj.callTheta
        if hasattr(obj, 'putTheta'): res['put_theta'] = obj.putTheta
        if hasattr(obj, 'callRho'): res['call_rho'] = obj.callRho
        if hasattr(obj, 'putRho'): res['put_rho'] = obj.putRho
        if hasattr(obj, 'vega'): res['vega'] = obj.vega
        if hasattr(obj, 'gamma'): res['gamma'] = obj.gamma
        
        # Implied Volatility
        if hasattr(obj, 'impliedVolatility'): res['implied_volatility'] = obj.impliedVolatility
        
        return res

    @staticmethod
    def calculate(model: str, args: list, volatility=None, callPrice=None, putPrice=None):
        """
        Run Mibian calculation.
        args: [Underlying, Strike, Interest, Days]
        kwargs: volatility OR callPrice OR putPrice
        """
        try:
            # Select Model Class
            model_cls = None
            if model == "BS": model_cls = mibian.BS
            elif model == "Me": model_cls = mibian.Me
            elif model == "GK": model_cls = mibian.GK
            else: raise ValueError(f"Unknown model: {model}")
            
            # Construct kwargs
            kwargs = {}
            if volatility is not None: kwargs['volatility'] = float(volatility)
            if callPrice is not None: kwargs['callPrice'] = float(callPrice)
            if putPrice is not None: kwargs['putPrice'] = float(putPrice)
            
            # Execute
            # Mibian takes list as first arg
            # args need to be floats
            clean_args = [float(x) for x in args]
            
            obj = model_cls(clean_args, **kwargs)
            return MibianCore._extract_results(obj)
            
        except Exception as e:
            raise ValueError(f"Mibian Error: {str(e)}")


def dict_to_json(data: dict, title: str = "Result") -> str:
    return json.dumps(data, indent=2)

def df_to_json(df: pd.DataFrame, title: str = "Result") -> str:
    return json.dumps(df.to_dict(orient='records'), indent=2)

