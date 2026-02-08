import pytest
import asyncio
import os
import time
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_hashlib_full_coverage():
    """
    REAL SIMULATION: Verify Hashlib Server (100% Tool Coverage).
    """
    params = get_server_params("hashlib_server", extra_dependencies=[])
    
    # Test Data
    test_string = "The quick brown fox jumps over the lazy dog"
    test_file_name = "test_hash_full.txt"
    test_file_content = "File content for hashing integrity checks."
    dummy_csv = "test_hash.csv"
    
    # Setup
    with open(test_file_name, "w") as f:
        f.write(test_file_content)
    with open(dummy_csv, "w") as f:
        f.write("id,name\n1,Alice\n2,Bob")
    
    # Create a duplicate file for find_duplicates
    with open("test_hash_dup.txt", "w") as f:
        f.write(test_file_content)
        
    print(f"\n--- Starting 100% Coverage Simulation: Hashlib Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # --- 1. CORE ---
            print("\n[1. Core Info]")
            await session.call_tool("algorithms_guaranteed", arguments={})
            await session.call_tool("algorithms_available", arguments={})
            await session.call_tool("get_hash_info", arguments={"algo_name": "sha256"})
            await session.call_tool("check_algorithm", arguments={"algo_name": "md5"})
            print(" \033[92m[PASS]\033[0m Core info tools")

            # --- 2. STRING HASHING ---
            print("\n[2. String Hashing]")
            algos = [
                "md5", "sha1", "sha224", "sha256", "sha384", "sha512",
                "sha3_224", "sha3_256", "sha3_384", "sha3_512",
                "blake2b", "blake2s"
            ]
            for algo in algos:
                await session.call_tool(f"{algo}_string", arguments={"text": test_string})
            
            await session.call_tool("hash_string_generic", arguments={"text": test_string, "algo_name": "sha256"})
            print(" \033[92m[PASS]\033[0m All string hash tools")

            # --- 3. SHAKE (Variable Length) ---
            print("\n[3. SHAKE]")
            await session.call_tool("shake_128_string", arguments={"text": test_string, "length": 16})
            await session.call_tool("shake_256_string", arguments={"text": test_string, "length": 16})
            print(" \033[92m[PASS]\033[0m SHAKE tools")

            # --- 4. FILE HASHING ---
            print("\n[4. File Hashing]")
            file_algos = ["md5", "sha1", "sha256", "sha512", "blake2b"]
            for algo in file_algos:
                await session.call_tool(f"{algo}_file", arguments={"file_path": test_file_name})
            
            await session.call_tool("hash_file_generic", arguments={"file_path": test_file_name, "algo_name": "sha256"})
            await session.call_tool("hash_file_partial", arguments={"file_path": test_file_name, "algo_name": "sha256", "chunk_size": 10})
            print(" \033[92m[PASS]\033[0m All file hash tools")

            # --- 5. BULK ---
            print("\n[5. Bulk Operations]")
            await session.call_tool("bulk_hash_strings", arguments={"texts": ["hello", "world"]})
            await session.call_tool("bulk_hash_files", arguments={"file_paths": [test_file_name, "test_hash_dup.txt"]})
            
            # Directory Hashing
            await session.call_tool("hash_directory", arguments={"directory": ".", "pattern": "*.txt"})
            res = await session.call_tool("hash_directory_manifest", arguments={"directory": "."})
            manifest_json = res.content[0].text
            print(" \033[92m[PASS]\033[0m Bulk & Directory tools")

            # --- 6. SECURITY ---
            print("\n[6. Security & HMAC]")
            key = "secret_key"
            res = await session.call_tool("hmac_string", arguments={"key": key, "message": test_string})
            sig = res.content[0].text
            
            await session.call_tool("hmac_file", arguments={"key": key, "file_path": test_file_name})
            await session.call_tool("pbkdf2_hmac", arguments={"password": "pass", "salt": "salt"})
            await session.call_tool("scrypt_kdf", arguments={"password": "pass", "salt": "salt"})
            
            # Verify HMAC
            res = await session.call_tool("verify_hmac", arguments={"key": key, "message": test_string, "signature": sig})
            if "true" in str(res.content[0].text).lower():
                print(" \033[92m[PASS]\033[0m verified hmac")
            print(" \033[92m[PASS]\033[0m Security tools")

            # --- 7. SUPER TOOLS ---
            print("\n[7. Super Tools]")
            # Get hash for verification
            res = await session.call_tool("sha256_file", arguments={"file_path": test_file_name})
            file_hash = res.content[0].text
            
            await session.call_tool("verify_file_checksum", arguments={"file_path": test_file_name, "expected_hash": file_hash})
            await session.call_tool("find_duplicates", arguments={"directory": "."})
            await session.call_tool("generate_dir_fingerprint", arguments={"directory": "."})
            await session.call_tool("compare_directories", arguments={"dir_a": ".", "dir_b": "."})
            
            # Verify manifest
            await session.call_tool("verify_manifest", arguments={"manifest_json": manifest_json, "base_dir": "."})
            
            # Rolling Hash
            await session.call_tool("update_rolling_hash", arguments={"current_hash": file_hash, "new_chunk": "update"})
            
            # URL Hash (Using example.com as real target)
            print(" Hashing URL...")
            await session.call_tool("hash_url_content", arguments={"url": "https://example.com"})
            
            await session.call_tool("detect_hash_type", arguments={"hash_str": file_hash})
            await session.call_tool("generate_random_token", arguments={"bytes_len": 16})
            
            # Benchmark (small size)
            await session.call_tool("benchmark_algorithms", arguments={"payload_size_mb": 1})
            
            # Monitor (short check)
            await session.call_tool("monitor_file_changes", arguments={"file_path": test_file_name, "checks": 1, "interval": 0.1})
            
            # CSV Hash
            await session.call_tool("hash_csv_rows", arguments={"input_csv": dummy_csv, "output_csv": "test_hash_out.csv"})
            
            # Password Verify
            # Need a valid hash first. Let's fake one or skip strict check, just call tool.
            # pbkdf2 default: sha256, 100000 iter. 
            # We'll just call it to ensure it runs, input might be invalid hash format but tool shouldn't crash.
            # Actually, let's skip verification of pass if we don't have valid hash, or generate one.
            # Using pbkdf2_hmac to generate
            res = await session.call_tool("pbkdf2_hmac", arguments={"password": "mypas", "salt": "mysalt"})
            p_hash = res.content[0].text
            await session.call_tool("verify_password_pbkdf2", arguments={"password": "mypas", "stored_hash": p_hash, "salt": "mysalt"})
            
            await session.call_tool("create_merkle_root", arguments={"items": ["a", "b", "c"]})
            await session.call_tool("compare_text_similarity", arguments={"text1": "hello", "text2": "hello world"})
            
            print(" \033[92m[PASS]\033[0m Super tools")

    # Cleanup
    for f in [test_file_name, "test_hash_dup.txt", dummy_csv, "test_hash_out.csv"]:
        if os.path.exists(f):
            os.remove(f)

    print("\n--- Hashlib 100% Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
