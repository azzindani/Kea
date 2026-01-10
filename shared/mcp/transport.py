"""
MCP Transport Layer.

Implements stdio and SSE transport for MCP communication.
"""

from __future__ import annotations

import asyncio
import json
import sys
from abc import ABC, abstractmethod
from typing import AsyncIterator

from shared.mcp.protocol import JSONRPCRequest, JSONRPCResponse, JSONRPCNotification


class Transport(ABC):
    """Abstract base class for MCP transport."""
    
    @abstractmethod
    async def send(self, message: JSONRPCRequest | JSONRPCResponse | JSONRPCNotification) -> None:
        """Send a message."""
        pass
    
    @abstractmethod
    async def receive(self) -> AsyncIterator[dict]:
        """Receive messages."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the transport."""
        pass


class StdioTransport(Transport):
    """
    Stdio transport for MCP communication.
    
    Reads from stdin, writes to stdout using newline-delimited JSON.
    """
    
    def __init__(self) -> None:
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._closed = False
    
    async def start(self) -> None:
        """Initialize stdio streams."""
        loop = asyncio.get_event_loop()
        self._reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(self._reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        transport, _ = await loop.connect_write_pipe(
            asyncio.Protocol, sys.stdout
        )
        self._writer = asyncio.StreamWriter(
            transport, protocol, self._reader, loop
        )
    
    async def send(self, message: JSONRPCRequest | JSONRPCResponse | JSONRPCNotification) -> None:
        """Send a message to stdout."""
        if self._writer is None:
            raise RuntimeError("Transport not started")
        
        data = message.model_dump_json() + "\n"
        self._writer.write(data.encode())
        await self._writer.drain()
    
    async def receive(self) -> AsyncIterator[dict]:
        """Receive messages from stdin."""
        if self._reader is None:
            raise RuntimeError("Transport not started")
        
        while not self._closed:
            try:
                line = await self._reader.readline()
                if not line:
                    break
                
                data = json.loads(line.decode().strip())
                yield data
            except json.JSONDecodeError:
                continue
            except Exception:
                break
    
    async def close(self) -> None:
        """Close the transport."""
        self._closed = True
        if self._writer:
            self._writer.close()


class SSETransport(Transport):
    """
    Server-Sent Events (SSE) transport for MCP communication.
    
    Used for HTTP-based streaming communication.
    """
    
    def __init__(self, url: str) -> None:
        self.url = url
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._closed = False
    
    async def send(self, message: JSONRPCRequest | JSONRPCResponse | JSONRPCNotification) -> None:
        """Send a message via HTTP POST."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            await client.post(
                self.url,
                json=message.model_dump(),
                headers={"Content-Type": "application/json"}
            )
    
    async def receive(self) -> AsyncIterator[dict]:
        """Receive messages via SSE stream."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", self.url) as response:
                async for line in response.aiter_lines():
                    if self._closed:
                        break
                    
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue
    
    async def close(self) -> None:
        """Close the transport."""
        self._closed = True
