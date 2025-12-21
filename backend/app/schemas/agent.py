"""
Agent Schemas

Pydantic schemas for CLI-agent communication.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class AgentHandshakeRequest(BaseModel):
    """Request schema for agent handshake"""
    
    server_id: str = Field(..., description="Current server ID from agent")
    agent_version: str = Field(..., description="CLI-agent version")
    hostname: str = Field(..., description="System hostname")
    
    class Config:
        json_schema_extra = {
            "example": {
                "server_id": "e1db3a86-b931-4520-baf2-d25634a59242",
                "agent_version": "1.0.0",
                "hostname": "my-server"
            }
        }


class AgentHandshakeResponse(BaseModel):
    """Response schema for agent handshake"""
    
    status: Literal["ok", "id_mismatch", "register_required"] = Field(
        ..., 
        description="Handshake status"
    )
    server_id: Optional[str] = Field(
        None, 
        description="Valid server ID (current or updated)"
    )
    old_id: Optional[str] = Field(
        None, 
        description="Old server ID (only for id_mismatch)"
    )
    message: str = Field(..., description="Human-readable message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "server_id": "be9662a4-bf98-4f2e-ace7-4743e579e35d",
                "message": "Server found, proceed with WebSocket"
            }
        }
