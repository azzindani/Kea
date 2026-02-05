
import asyncio
import json
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mcp_servers.python_server.tools.execute_code import execute_code_tool
# We'll mock the scraper output since we can't easily run playwright in this simple script without a server
# But we can verify execute_code can parse a JSON string input if we were to simulate a chain.

async def verify_io_chain():
    print("🧪 Verifying I/O Standardization...")
    
    # 1. Simulate Scraper Output (JSON String)
    scraper_output = json.dumps({
        "url": "https://example.com",
        "status": 200,
        "content": "The price of AAPL is $150.50 today.",
        "tables": [],
        "metadata": {"title": "Example"}
    })
    
    print(f"INPUT (From Scraper): {scraper_output[:100]}...")
    
    # 2. Simulate Python Tool receiving this data structure
    # The 'Planner' would likely extract the 'content' field or pass the whole object.
    # Let's verify 'execute_code' can output JSON.
    
    code = f"""
import json
data = json.loads('''{scraper_output}''')
print(f"Extracted Content: {{data['content']}}")
    """
    
    print("\nRUNNING Python Tool...")
    result = await execute_code_tool({"code": code})
    
    # 3. Verify Output is JSON
    try:
        # The result.content[0].text should be a JSON string now
        output_text = result.content[0].text
        print(f"OUTPUT (From Python): {output_text[:100]}...")
        
        output_json = json.loads(output_text)  # Should parse
        
        if output_json["status"] == "success":
            print("\n✅ Verification SUCCESS: Output is valid JSON.")
            print(f"Stdout output: {output_json['stdout']}")
        else:
            print(f"\n❌ Verification FAILED: Status is {output_json.get('status')}")
            
    except json.JSONDecodeError:
        print("\n❌ Verification FAILED: Output is NOT valid JSON.")
        print(f"Raw Output: {output_text}")
    except Exception as e:
        print(f"\n❌ Verification ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(verify_io_chain())
