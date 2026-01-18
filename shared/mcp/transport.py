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
    Compatible with Windows ProactorEventLoop via run_in_executor.
    """
    
    def __init__(self) -> None:
        self._loop = None
        self._closed = False
    
    async def start(self) -> None:
        """Initialize."""
        self._loop = asyncio.get_event_loop()
        # No special setup needed for executor-based reading
        
    async def send(self, message: JSONRPCRequest | JSONRPCResponse | JSONRPCNotification) -> None:
        """Send a message to stdout."""
        # Use sys.stdout.write directly to avoid async pipe issues on Windows
        data = message.model_dump_json() + "\n"
        sys.stdout.write(data)
        sys.stdout.flush()
    
    async def receive(self) -> AsyncIterator[dict]:
        """Receive messages from stdin."""
        if not self._loop:
             self._loop = asyncio.get_event_loop()
             
        while not self._closed:
            try:
                # Run blocking readline in executor to avoid blocking the loop
                # and to avoid Windows Proactor pipe issues
                line = await self._loop.run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    yield data
                except json.JSONDecodeError:
                    continue
                    
            except Exception:
                break
    
    async def close(self) -> None:
        """Close the transport."""
        self._closed = True


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


class SubprocessTransport(Transport):
    """
    Transport for communicating with a local subprocess.
    """
    
    def __init__(self, process: asyncio.subprocess.Process) -> None:
        self.process = process
        self._reader = process.stdout
        self._writer = process.stdin
        self._closed = False
        
    async def send(self, message: JSONRPCRequest | JSONRPCResponse | JSONRPCNotification) -> None:
        """Send message to subprocess stdin."""
        if self._closed or not self._writer:
            raise RuntimeError("Transport is closed")
            
        data = message.model_dump_json() + "\n"
        self._writer.write(data.encode())
        await self._writer.drain()
        
    async def receive(self) -> AsyncIterator[dict]:
        """Receive messages from subprocess stdout."""
        if not self._reader:
            raise RuntimeError("Transport not initialized")
            
        while not self._closed:
            try:
                line = await self._reader.readline()
                if not line:
                    break
                    
                line_str = line.decode().strip()
                if not line_str:
                    continue
                    
                try:
                    data = json.loads(line_str)
                    yield data
                except json.JSONDecodeError:
                    # Ignore debug output that isn't JSON
                    pass
            except Exception:
                break
                
    async def close(self) -> None:
        """Close the transport."""
        self._closed = True
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
