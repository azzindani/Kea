from typing import Any
from mcp_servers.docx_server.tools.core_ops import open_document, save_document, get_document_properties, set_document_properties

# We can expose more specific property tools if needed, but core_ops covers the basics.
# Let's add custom properties tool if python-docx supports it (it does to some extent).

def get_custom_property(path: str, name: str) -> Any:
    """Get a custom document property."""
    # python-docx has patchy support for custom props depending on version/extension.
    # We'll skip complex custom props for now to ensure stability.
    pass

# For now, we will re-export core properties ops here if we wanted separation, 
# but they are logically in core. 
# We'll stick to core_ops for properties for simplicity.
