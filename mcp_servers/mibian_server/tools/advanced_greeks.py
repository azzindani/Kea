
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_result

def _calc_raw(model, args, vol):
    return MibianCore.calculate(model, args, volatility=vol)

async def calculate_advanced_greeks(arguments: dict) -> ToolResult:
    """
    Calculate 2nd/3rd Order Greeks via Finite Difference.
    - Vanna: dDelta/dVol
    - Charm: dDelta/dTime
    - Vomma: dVega/dVol
    - Speed: dGamma/dSpot
    - Zomma: dGamma/dVol
    """
    try:
        model = "BS" # Default to BS, could param
        u = arguments['underlying']
        s = arguments['strike']
        r = arguments['interest']
        d = arguments['days']
        v = arguments['volatility']
        
        # Base
        base = _calc_raw(model, [u, s, r, d], v)
        
        # Perturbations
        du = u * 0.01 # 1% price move
        dv = 0.01     # 1% vol move (e.g. 20 -> 20.01) (Wait, Mibian input is 20 for 20%? Yes)
        dt = 1.0      # 1 day move
        
        # Vanna: (Delta(v+dv) - Delta(v-dv)) / 2dv
        # Or simple forward: (Delta(v+dv) - Delta) / dv
        res_v_plus = _calc_raw(model, [u, s, r, d], v + dv)
        
        vanna_call = (res_v_plus['call_delta'] - base['call_delta']) / dv
        vanna_put = (res_v_plus['put_delta'] - base['put_delta']) / dv
        
        # Vomma: (Vega(v+dv) - Vega) / dv
        vomma = (res_v_plus['vega'] - base['vega']) / dv
        
        # Charm: -(Delta(t-dt) - Delta(t)) / dt  (Time passing decreases days)
        # Days decrease by 1
        if d > 1:
            res_t_minus = _calc_raw(model, [u, s, r, d - dt], v)
            charm_call = -(res_t_minus['call_delta'] - base['call_delta']) / dt # per day
            charm_put = -(res_t_minus['put_delta'] - base['put_delta']) / dt
        else:
            charm_call = 0
            charm_put = 0
            
        # Speed: (Gamma(u+du) - Gamma) / du
        res_u_plus = _calc_raw(model, [u + du, s, r, d], v)
        speed = (res_u_plus['gamma'] - base['gamma']) / du
        
        # Zomma: (Gamma(v+dv) - Gamma) / dv
        zomma = (res_v_plus['gamma'] - base['gamma']) / dv
        
        return dict_to_result({
            "vanna_call": vanna_call,
            "vanna_put": vanna_put,
            "vomma": vomma,
            "charm_call": charm_call,
            "charm_put": charm_put,
            "speed": speed,
            "zomma": zomma
        }, "Advanced Greeks")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# Wrapper aliases
async def calculate_vanna(arguments: dict) -> ToolResult: return await calculate_advanced_greeks(arguments)
async def calculate_vomma(arguments: dict) -> ToolResult: return await calculate_advanced_greeks(arguments)
async def calculate_charm(arguments: dict) -> ToolResult: return await calculate_advanced_greeks(arguments)
async def calculate_speed(arguments: dict) -> ToolResult: return await calculate_advanced_greeks(arguments)
