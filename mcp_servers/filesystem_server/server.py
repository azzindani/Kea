
"""
MCP Filesystem Server (Virtual File System).

This server provides a "Windows Explorer" like interface for the AI.
It maps virtual paths (e.g. /projects/stocks/analysis.csv) to physical Artifact IDs.
"""

from __future__ import annotations

import os
import asyncio
import json
import mimetypes
from pathlib import Path
from typing import Any, Optional

import asyncpg
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Initialize Logger
logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

class FilesystemServer(MCPServer):
    """MCP Server for Virtual File System operations."""
    
    def __init__(self) -> None:
        super().__init__(name="filesystem_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register filesystem tools."""
        
        self.register_tool(
            name="fs_init",
            description="Initialize the VFS database schema (Idempotent).",
            handler=self.fs_init,
            parameters={}
        )
        
        self.register_tool(
            name="fs_ls",
            description="List files and folders in a directory.",
            handler=self.fs_ls,
            parameters={
                "path": {
                    "type": "string",
                    "description": "The directory path (e.g. '/projects' or '/'). Default: '/'"
                }
            }
        )
        
        self.register_tool(
            name="fs_mkdir",
            description="Create a new folder.",
            handler=self.fs_mkdir,
            parameters={
                "path": {
                    "type": "string",
                    "description": "Full path of the folder (e.g. '/projects/new_project')"
                }
            },
            required=["path"]
        )
        
        self.register_tool(
            name="fs_write",
            description="Write content to a file (Virtual & Physical).",
            handler=self.fs_write,
            parameters={
                "path": {
                    "type": "string",
                    "description": "Full path (e.g. '/notes/thought.txt')"
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the file. Default: ''"
                }
            },
            required=["path", "content"]
        )
        
        self.register_tool(
            name="fs_read",
            description="Read content of a file.",
            handler=self.fs_read,
            parameters={
                "path": {
                    "type": "string",
                    "description": "Full path to read"
                }
            },
            required=["path"]
        )
        
        
    async def fs_init(self, arguments: dict) -> ToolResult:
        if not DATABASE_URL:
            return ToolResult(content=[TextContent(text="Error: DATABASE_URL not set.")], isError=True)
            
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS file_system (
                    id SERIAL PRIMARY KEY,
                    path TEXT NOT NULL UNIQUE,
                    parent_folder TEXT,
                    artifact_id TEXT,
                    file_type TEXT CHECK (file_type IN ('file', 'folder')),
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
                CREATE INDEX IF NOT EXISTS idx_vfs_path ON file_system(path);
                CREATE INDEX IF NOT EXISTS idx_vfs_parent ON file_system(parent_folder);
            """)
            return ToolResult(content=[TextContent(text="VFS Schema Initialized.")])
        finally:
            await conn.close()

    async def fs_ls(self, arguments: dict) -> ToolResult:
        path = arguments.get("path", "/")
        if not DATABASE_URL:
             return ToolResult(content=[TextContent(text="Error: DATABASE_URL not set.")], isError=True)
            
        # Normalize path (remove trailing slash unless root)
        clean_path = path.rstrip("/") if path != "/" else "/"
        
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch("""
                SELECT path, file_type, artifact_id, metadata 
                FROM file_system 
                WHERE parent_folder = $1 OR (parent_folder IS NULL AND $1 = '/')
                ORDER BY file_type DESC, path ASC
            """, clean_path)
            
            if not rows:
                # Check if directory exists at least
                exists = await conn.fetchval("SELECT 1 FROM file_system WHERE path = $1 AND file_type = 'folder'", clean_path)
                if not exists and clean_path != "/":
                     return ToolResult(content=[TextContent(text=f"Error: Directory '{clean_path}' does not exist.")], isError=True)
                return ToolResult(content=[TextContent(text="[]")])
                
            result = []
            for row in rows:
                name = row["path"].rstrip("/").split("/")[-1]
                result.append({
                    "name": name,
                    "type": row["file_type"],
                    "path": row["path"],
                    "id": row["artifact_id"]
                })
                
            return ToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        finally:
            await conn.close()

    async def fs_mkdir(self, arguments: dict) -> ToolResult:
        path = arguments["path"]
        if not DATABASE_URL:
             return ToolResult(content=[TextContent(text="Error: DATABASE_URL not set.")], isError=True)
            
        clean_path = path.rstrip("/")
        parent = "/" + "/".join(clean_path.strip("/").split("/")[:-1])
        if parent == "//": parent = "/" # Fix root parent
        
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute("""
                INSERT INTO file_system (path, parent_folder, file_type, metadata)
                VALUES ($1, $2, 'folder', '{}'::jsonb)
                ON CONFLICT (path) DO NOTHING
            """, clean_path, parent)
            return ToolResult(content=[TextContent(text=f"Folder created: {clean_path}")])
        except Exception as e:
            return ToolResult(content=[TextContent(text=f"Error creating folder: {e}")], isError=True)
        finally:
            await conn.close()

    async def fs_write(self, arguments: dict) -> ToolResult:
        path = arguments["path"]
        content = arguments["content"]
        description = arguments.get("description", "")
        
        # 1. Save Physical Artifact (Mocking via File System for now, should use KeaClient)
        # We will write to ./artifacts locally to be compatible with existing setup
        
        local_artifacts_dir = Path("artifacts")
        local_artifacts_dir.mkdir(exist_ok=True)
        
        filename = Path(path).name
        import uuid
        artifact_id = f"vfs-{uuid.uuid4().hex[:8]}"
        
        # Save content
        file_path = local_artifacts_dir / f"{artifact_id}_{filename}"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # 2. Register in VFS (Postgres)
        if not DATABASE_URL:
             return ToolResult(content=[TextContent(text="Error: DATABASE_URL not set (Saved locally though).")], isError=True)
            
        clean_path = path
        parent = "/" + "/".join(clean_path.strip("/").split("/")[:-1])
        if parent == "//": parent = "/"
        
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Ensure parent exists
            await conn.execute("""
                INSERT INTO file_system (path, parent_folder, file_type, metadata)
                VALUES ($1, $2, 'folder', '{}'::jsonb)
                ON CONFLICT (path) DO NOTHING
            """, parent, "/" if parent != "/" else None) # Simple parent fix
            
            # Save file record
            await conn.execute("""
                INSERT INTO file_system (path, parent_folder, artifact_id, file_type, metadata)
                VALUES ($1, $2, $3, 'file', $4)
                ON CONFLICT (path) DO UPDATE SET 
                    artifact_id = EXCLUDED.artifact_id,
                    created_at = NOW()
            """, clean_path, parent, artifact_id, json.dumps({"description": description, "local_path": str(file_path)}))
            
            return ToolResult(content=[TextContent(text=f"File saved: {path} (ID: {artifact_id})")])
        finally:
            await conn.close()

    async def fs_read(self, arguments: dict) -> ToolResult:
        path = arguments["path"]
        if not DATABASE_URL:
             return ToolResult(content=[TextContent(text="Error: DATABASE_URL not set.")], isError=True)
            
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            row = await conn.fetchrow("SELECT artifact_id, metadata FROM file_system WHERE path = $1", path)
            if not row:
                return ToolResult(content=[TextContent(text=f"Error: File not found at {path}")], isError=True)
                
            meta = json.loads(row["metadata"])
            local_path = meta.get("local_path")
            
            if local_path and os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    return ToolResult(content=[TextContent(text=f.read())])
            
            return ToolResult(content=[TextContent(text=f"Error: Physical file missing for {path} (ID: {row['artifact_id']})")], isError=True)
        finally:
            await conn.close()

async def main() -> None:
    """Run the filesystem server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="filesystem_server"))
    
    server = FilesystemServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
