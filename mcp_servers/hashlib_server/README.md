# 🔌 Hashlib Server

The `hashlib_server` is an MCP server providing tools for **Hashlib Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `algorithms_guaranteed` | Execute algorithms guaranteed operation | `` |
| `algorithms_available` | Execute algorithms available operation | `` |
| `get_hash_info` | Execute get hash info operation | `algo_name: str` |
| `check_algorithm` | Execute check algorithm operation | `algo_name: str` |
| `md5_string` | Execute md5 string operation | `text: str` |
| `sha1_string` | Execute sha1 string operation | `text: str` |
| `sha224_string` | Execute sha224 string operation | `text: str` |
| `sha256_string` | Execute sha256 string operation | `text: str` |
| `sha384_string` | Execute sha384 string operation | `text: str` |
| `sha512_string` | Execute sha512 string operation | `text: str` |
| `sha3_224_string` | Execute sha3 224 string operation | `text: str` |
| `sha3_256_string` | Execute sha3 256 string operation | `text: str` |
| `sha3_384_string` | Execute sha3 384 string operation | `text: str` |
| `sha3_512_string` | Execute sha3 512 string operation | `text: str` |
| `blake2b_string` | Execute blake2b string operation | `text: str, digest_size: int = 64` |
| `blake2s_string` | Execute blake2s string operation | `text: str, digest_size: int = 32` |
| `hash_string_generic` | Execute hash string generic operation | `text: str, algo_name: str` |
| `shake_128_string` | Execute shake 128 string operation | `text: str, length: int` |
| `shake_256_string` | Execute shake 256 string operation | `text: str, length: int` |
| `md5_file` | Execute md5 file operation | `file_path: str` |
| `sha1_file` | Execute sha1 file operation | `file_path: str` |
| `sha256_file` | Execute sha256 file operation | `file_path: str` |
| `sha512_file` | Execute sha512 file operation | `file_path: str` |
| `blake2b_file` | Execute blake2b file operation | `file_path: str` |
| `hash_file_generic` | Execute hash file generic operation | `file_path: str, algo_name: str` |
| `hash_file_partial` | Execute hash file partial operation | `file_path: str, algo_name: str, chunk_size: int = 1024` |
| `bulk_hash_strings` | Execute bulk hash strings operation | `texts: List[str], algo: str = "sha256"` |
| `bulk_hash_files` | Execute bulk hash files operation | `file_paths: List[str], algo: str = "sha256"` |
| `hash_directory` | Execute hash directory operation | `directory: str, algo: str = "sha256", recursive: bool = True, pattern: str = "*"` |
| `hash_directory_manifest` | Execute hash directory manifest operation | `directory: str, algo: str = "sha256"` |
| `hmac_string` | Execute hmac string operation | `key: str, message: str, algo: str = "sha256"` |
| `hmac_file` | Execute hmac file operation | `key: str, file_path: str, algo: str = "sha256"` |
| `pbkdf2_hmac` | Execute pbkdf2 hmac operation | `password: str, salt: str, iterations: int = 100000, dklen: int = 32, algo: str = "sha256"` |
| `scrypt_kdf` | Execute scrypt kdf operation | `password: str, salt: str, n: int = 16384, r: int = 8, p: int = 1, dklen: int = 32` |
| `verify_hmac` | Execute verify hmac operation | `key: str, message: str, signature: str, algo: str = "sha256"` |
| `verify_file_checksum` | Execute verify file checksum operation | `file_path: str, expected_hash: str, algo: str = "sha256"` |
| `find_duplicates` | Execute find duplicates operation | `directory: str, algo: str = "sha256"` |
| `generate_dir_fingerprint` | Execute generate dir fingerprint operation | `directory: str, algo: str = "sha256"` |
| `compare_directories` | Execute compare directories operation | `dir_a: str, dir_b: str, algo: str = "sha256"` |
| `verify_manifest` | Execute verify manifest operation | `manifest_json: str, base_dir: str` |
| `update_rolling_hash` | Execute update rolling hash operation | `current_hash: str, new_chunk: str, algo: str = "sha256"` |
| `hash_url_content` | Execute hash url content operation | `url: str, algo: str = "sha256"` |
| `detect_hash_type` | Execute detect hash type operation | `hash_str: str` |
| `generate_random_token` | Execute generate random token operation | `bytes_len: int = 32` |
| `benchmark_algorithms` | Execute benchmark algorithms operation | `payload_size_mb: int = 10` |
| `monitor_file_changes` | Execute monitor file changes operation | `file_path: str, checks: int = 3, interval: float = 1.0` |
| `hash_csv_rows` | Execute hash csv rows operation | `input_csv: str, output_csv: str, algo: str = "sha256"` |
| `verify_password_pbkdf2` | Execute verify password pbkdf2 operation | `password: str, stored_hash: str, salt: str, iterations: int = 100000` |
| `create_merkle_root` | Execute create merkle root operation | `items: List[str], algo: str = "sha256"` |
| `compare_text_similarity` | Execute compare text similarity operation | `text1: str, text2: str` |

## 📦 Dependencies

Standard library only.

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.hashlib_server.server
```
