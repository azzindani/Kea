
import os
import json
import asyncio
import asyncpg
from pathlib import Path
from shared.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db() -> str:
    """Initialize the VFS database schema."""
    if not DATABASE_URL:
        return "Error: DATABASE_URL not set."
        
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
        return "VFS Schema Initialized."
    except Exception as e:
        return f"Error initializing DB: {e}"
    finally:
        await conn.close()

async def list_files(path: str = "/") -> str:
    """List files and folders in a directory."""
    if not DATABASE_URL:
        return "Error: DATABASE_URL not set."
        
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
                 return f"Error: Directory '{clean_path}' does not exist."
            return "[]"
            
        result = []
        for row in rows:
            name = row["path"].rstrip("/").split("/")[-1]
            result.append({
                "name": name,
                "type": row["file_type"],
                "path": row["path"],
                "id": row["artifact_id"]
            })
            
        return json.dumps(result, indent=2)
    finally:
        await conn.close()

async def make_directory(path: str) -> str:
    """Create a new folder."""
    if not DATABASE_URL:
         return "Error: DATABASE_URL not set."
        
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
        return f"Folder created: {clean_path}"
    except Exception as e:
        return f"Error creating folder: {e}"
    finally:
        await conn.close()

async def write_file(path: str, content: str, description: str = "") -> str:
    """Write content to a file (Virtual & Physical)."""
    # 1. Save Physical Artifact (Mocking via File System for now, should use KeaClient)
    # We will write to ./artifacts locally to be compatible with existing setup
    
    local_artifacts_dir = Path("artifacts")
    local_artifacts_dir.mkdir(exist_ok=True)
    
    filename = Path(path).name
    import uuid
    artifact_id = f"vfs-{uuid.uuid4().hex[:8]}"
    
    # Save content
    file_path = local_artifacts_dir / f"{artifact_id}_{filename}"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"Error writing local file: {e}"
        
    # 2. Register in VFS (Postgres)
    if not DATABASE_URL:
         return "Error: DATABASE_URL not set (Saved locally though)."
        
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
        
        return f"File saved: {path} (ID: {artifact_id})"
    except Exception as e:
        return f"Error updating DB: {e}"
    finally:
        await conn.close()

async def read_file(path: str) -> str:
    """Read content of a file."""
    if not DATABASE_URL:
         return "Error: DATABASE_URL not set."
        
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT artifact_id, metadata FROM file_system WHERE path = $1", path)
        if not row:
            return f"Error: File not found at {path}"
            
        meta = json.loads(row["metadata"])
        local_path = meta.get("local_path")
        
        if local_path and os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                return f.read()
        
        return f"Error: Physical file missing for {path} (ID: {row['artifact_id']})"
    except Exception as e:
        return f"Error reading file: {e}"
    finally:
        await conn.close()
