
from shared.mcp.protocol import ToolResult, TextContent
from eth_account import Account
import secrets

async def generate_wallet(arguments: dict) -> ToolResult:
    """
    Generate a new random Web3 Wallet.
    RETURNS PRIVATE KEY - CAUTION.
    """
    try:
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        acct = Account.from_key(private_key)
        return ToolResult(content=[TextContent(text=f"### New Wallet Generated\n**Address**: {acct.address}\n**Private Key**: {private_key}\n\n**SAVE THIS SECURELY. IT WILL NOT BE SHOWN AGAIN.**")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
