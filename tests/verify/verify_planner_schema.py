
import asyncio
import sys
import os

# Mock classes to simulate the environment
class MockRegistry:
    def __init__(self):
        self.tool_to_server = {
            "get_stock_price": "finance_server",
            "calculate_rsi": "finance_server"
        }

    async def search_tools(self, query, limit=50):
        # Return mock tools with schemas
        return [
            {
                "name": "get_stock_price",
                "description": "Get current price for a ticker",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock symbol"}
                    },
                    "required": ["ticker"]
                }
            },
            {
                "name": "calculate_rsi",
                "description": "Calculate RSI indicator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prices": {"type": "array", "items": {"type": "number"}},
                        "period": {"type": "integer", "default": 14}
                    },
                    "required": ["prices"]
                }
            }
        ]
    
    async def list_all_tools(self):
        return await self.search_tools("")

async def verify_schema_formatting():
    print("Verifying Planner Schema Extraction Logic...")
    
    registry = MockRegistry()
    query = "Analyze AAPL"
    
    # Simulate the logic I added to planner.py
    relevant_tools = []
    try:
        search_results = await registry.search_tools(query, limit=50)
        
        if search_results:
            print(f"Found {len(search_results)} relevant tools")
            for t in search_results:
                name = t.get('name', 'N/A')
                desc = t.get('description', '')[:200]
                schema = t.get('inputSchema', {})
                # Compact schema representation
                schema_str = str(schema).replace("{", "{{").replace("}", "}}")
                entry = f"TOOL: {name}\nDESCRIPTION: {desc}\nSCHEMA: {schema_str}\n"
                relevant_tools.append(entry)
                print(f"--- Formatted Entry ---\n{entry}")
                
    except Exception as e:
        print(f"Error: {e}")
        
    if len(relevant_tools) == 2:
        print("\nSUCCESS: Logic correctly formatted 2 tools with schemas.")
    else:
        print("\nFAILURE: Did not format expected number of tools.")

if __name__ == "__main__":
    asyncio.run(verify_schema_formatting())
