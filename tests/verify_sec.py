
import asyncio
from mcp_servers.sec_edgar_server.server import SecEdgarServer
import os

async def verify():
    server = SecEdgarServer()
    print("--- Verifying SEC-Edgar Server ---")
    print(f"Total Tools: {len(server.get_tools())}")

    # 1. Test Download (10-K for AAPL)
    print("\n--- 1. Testing Download (AAPL 10-K) ---")
    try:
        handler = server._handlers["download_10k_latest"]
        # Limit 1
        res = await handler({"ticker": "AAPL", "amount": 1})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
             # Wait a moment for file system?
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test Listing
    print("\n--- 2. Testing Listing ---")
    try:
        handler = server._handlers["list_downloaded_filings"]
        res = await handler({"ticker": "AAPL", "filing_type": "10-K"})
        if not res.isError:
            import json
            files = json.loads(res.content[0].text)
            print(f"Found {len(files)} files.")
            if len(files) > 0:
                global valid_path
                valid_path = files[0]['path']
                print(f"Sample Path: {valid_path}")
            else:
                print("No files found!")
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 3. Test Reading
    print("\n--- 3. Testing Reading ---")
    try:
        if 'valid_path' in globals():
            handler = server._handlers["read_filing_content"]
            res = await handler({"path": valid_path, "max_chars": 500})
            if not res.isError:
                 print("SUCCESS content snippet:", res.content[0].text[:200])
            else:
                 print("FAILED:", res.content[0].text)
        else:
            print("Skipping read test (no path).")
    except Exception as e:
        print(f"Error: {e}")

    # 4. Test Metadata Extraction (Phase 2)
    print("\n--- 4. Testing Metadata Extraction ---")
    try:
        if 'valid_path' in globals():
            handler = server._handlers["extract_filing_metadata"]
            res = await handler({"path": valid_path})
            if not res.isError:
                 print("SUCCESS snippet:", res.content[0].text[:500])
            else:
                 print("FAILED:", res.content[0].text)
        else:
            print("Skipping metadata test (no path).")
    except Exception as e:
        print(f"Error: {e}")

    # 5. Test Structured Parsing (Form 4)
    print("\n--- 5. Testing Form 4 Download & Parse ---")
    try:
        # Download Form 4 first
        dl_handler = server._handlers["download_form_4"]
        res = await dl_handler({"ticker": "AAPL", "amount": 1})
        if res.isError:
            print("Download Failed:", res.content[0].text)
        else:
            print("Download Success. Finding file...")
            # Find the file
            list_handler = server._handlers["list_downloaded_filings"]
            res = await list_handler({"ticker": "AAPL", "filing_type": "4"})
            
            import json
            files = json.loads(res.content[0].text)
            if len(files) > 0:
                f4_path = files[0]['path']
                print(f"Parsing: {f4_path}")
                
                parse_handler = server._handlers["parse_form4_transactions"]
                res = await parse_handler({"path": f4_path})
                if not res.isError:
                     print("SUCCESS PARSE snippet:", res.content[0].text[:500])
                else:
                     print("PARSE FAILED:", res.content[0].text)
            else:
                print("No Form 4 found.")
    except Exception as e:
        print(f"Error: {e}")

    # 6. Test Sentiment Analysis (Phase 4)
    print("\n--- 6. Testing Sentiment (AAPL 10-K) ---")
    try:
        # We need the 10-K path
        list_handler = server._handlers["list_downloaded_filings"]
        res = await list_handler({"ticker": "AAPL", "filing_type": "10-K"})
        
        import json
        files = json.loads(res.content[0].text)
        if len(files) > 0:
            k_path = files[0]['path']
            
            # Extract Item 7 (MD&A)
            print("Extracting MD&A...")
            extract_handler = server._handlers["extract_filing_section"]
            res = await extract_handler({"path": k_path, "item": "7"})
            
            if not res.isError:
                data = json.loads(res.content[0].text)
                if data.get("found"):
                    preview = data.get("text_preview", "")
                    print(f"Extraction Success ({data.get('text_length')} chars). Preview: {preview[:100]}...")
                    
                    # Analyze Sentiment
                    sent_handler = server._handlers["calculate_filing_sentiment"]
                    # We can pass path or text. Let's pass path to analyze WHOLE 10-K for now (easier)
                    res = await sent_handler({"path": k_path})
                    if not res.isError:
                        print("SENTIMENT snippet:", res.content[0].text[:500])
                    else:
                        print("SENTIMENT FAILED:", res.content[0].text)
                else:
                    print("Section extraction found nothing (heuristic failed).")
            else:
                print("Extraction Error:", res.content[0].text)
                
        else:
             print("No 10-K found to analyze.")
    except Exception as e:
        print(f"Error: {e}")

    # 7. Test Discovery (Phase 5)
    print("\n--- 7. Testing Local Library Discovery ---")
    try:
        handler = server._handlers["scan_local_library"]
        res = await handler({})
        if not res.isError:
             print("DISCOVERY snippet:", res.content[0].text[:500])
        else:
             print("DISCOVERY FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 8. Test Readability (Phase 6)
    print("\n--- 8. Testing Readability (AAPL 10-K) ---")
    try:
        # Re-using discovery logic or just hardcoded known path if we had one
        # Let's use search_local_library to find it
        search_handler = server._handlers["search_local_library"]
        res = await search_handler({"query": "Apple", "ticker": "AAPL"})
        
        if not res.isError:
             import json
             data = json.loads(res.content[0].text)
             if data.get("found_files"):
                 target = data['found_files'][0]
                 print(f"Targeting: {target}")
                 
                 read_handler = server._handlers["calculate_readability_metrics"]
                 res = await read_handler({"path": target})
                 if not res.isError:
                      print("READABILITY snippet:", res.content[0].text[:500])
                 else:
                      print("READABILITY FAILED:", res.content[0].text)
             else:
                 print("No files found via search.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
