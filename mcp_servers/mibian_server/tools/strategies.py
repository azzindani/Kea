
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_json


async def calculate_strategy_price(legs: list[dict]) -> str:
    """
    Calculate Multi-Leg Strategy Price & Greeks.
    Args:
        legs: List of dicts. Each dict:
              - type: "call" or "put"
              - price_model: "BS", "GK", "Me" (default BS)
              - side: "long" or "short" (multiplier 1 or -1)
              - quantity: number of contracts (default 1)
              - underlying, strike, interest, days, volatility
    """
    try:
        legs_input = legs # arguments.get("legs", [])
        
        total_data = {
            "price": 0.0,
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0
        }
        
        leg_details = []
        
        for i, leg in enumerate(legs_input):
            model = leg.get("price_model", "BS")
            side_mult = 1 if leg.get("side", "long").lower() == "long" else -1
            qty = leg.get("quantity", 1)
            multiplier = side_mult * qty
            
            # Calc
            args = [leg['underlying'], leg['strike'], leg['interest'], leg['days']]
            res = MibianCore.calculate(model, args, volatility=leg['volatility'])
            
            # Extract
            l_type = leg.get("type", "call").lower()
            price = res.get(f"{l_type}_price", 0)
            delta = res.get(f"{l_type}_delta", 0)
            theta = res.get(f"{l_type}_theta", 0)
            rho = res.get(f"{l_type}_rho", 0)
            
            # Gamma/Vega are same for call/put usually in BS
            gamma = res.get("gamma", 0)
            vega = res.get("vega", 0)
            
            # Aggregate
            total_data['price'] += price * multiplier
            total_data['delta'] += delta * multiplier
            total_data['gamma'] += gamma * multiplier
            total_data['theta'] += theta * multiplier
            total_data['vega'] += vega * multiplier
            total_data['rho'] += rho * multiplier
            
            leg_details.append({
                "leg": i+1,
                "type": l_type,
                "side": leg.get("side", "long"),
                "individual_price": price,
                "contribution": price * multiplier
            })
            
        return dict_to_json({
            "strategy_totals": total_data,
            "legs": leg_details
        }, "Strategy Analysis")
        
    except Exception as e:
        return f"Error: {str(e)}"

