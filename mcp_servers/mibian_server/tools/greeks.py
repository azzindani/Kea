
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_json


async def _calc_greek(arguments: dict, model: str, greek: str) -> str:
    try:
        min_args = ['underlying', 'strike', 'interest', 'days', 'volatility']
        for a in min_args:
             if a not in arguments: raise ValueError(f"Missing argument: {a}")
             
        args = [arguments['underlying'], arguments['strike'], arguments['interest'], arguments['days']]
        res = MibianCore.calculate(model, args, volatility=arguments['volatility'])
        
        # Filter purely for the requested greek(s)
        # If greek="delta", return call_delta and put_delta
        filtered = {}
        if greek == "delta":
            filtered = {'call_delta': res.get('call_delta'), 'put_delta': res.get('put_delta')}
        elif greek == "theta":
            filtered = {'call_theta': res.get('call_theta'), 'put_theta': res.get('put_theta')}
        elif greek == "rho":
            filtered = {'call_rho': res.get('call_rho'), 'put_rho': res.get('put_rho')}
        elif greek == "gamma":
            filtered = {'gamma': res.get('gamma')}
        elif greek == "vega":
            filtered = {'vega': res.get('vega')}
        else:
            filtered = res
            
        return dict_to_json(filtered, f"{model} {greek}")
    except Exception as e:
        return f"Error: {str(e)}"


# Wrappers

# Wrappers
async def calculate_bs_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str: return await _calc_greek({"underlying": underlying, "strike": strike, "interest": interest, "days": days, "volatility": volatility}, "BS", "delta")
async def calculate_bs_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str: return await _calc_greek({"underlying": underlying, "strike": strike, "interest": interest, "days": days, "volatility": volatility}, "BS", "theta")
async def calculate_bs_gamma(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str: return await _calc_greek({"underlying": underlying, "strike": strike, "interest": interest, "days": days, "volatility": volatility}, "BS", "gamma")
async def calculate_bs_vega(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str: return await _calc_greek({"underlying": underlying, "strike": strike, "interest": interest, "days": days, "volatility": volatility}, "BS", "vega")
async def calculate_bs_rho(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str: return await _calc_greek({"underlying": underlying, "strike": strike, "interest": interest, "days": days, "volatility": volatility}, "BS", "rho")

async def calculate_gk_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str: return await _calc_greek({"underlying": underlying, "strike": strike, "interest": interest, "days": days, "volatility": volatility}, "GK", "delta")
async def calculate_gk_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str: return await _calc_greek({"underlying": underlying, "strike": strike, "interest": interest, "days": days, "volatility": volatility}, "GK", "theta")
# ... Add others as needed

