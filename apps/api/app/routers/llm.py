"""BYO LLM key management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.llm_credential import LlmCredential
from app.crypto import encrypt_value, decrypt_value

router = APIRouter()


class LlmKeyCreate(BaseModel):
    provider: str = "openai"
    api_key: str
    model: Optional[str] = "gpt-4o-mini"


class LlmKeyResponse(BaseModel):
    provider: str
    key_last4: str
    model: str
    created_at: str
    last_verified_at: Optional[str]
    last_used_at: Optional[str]


class LlmKeyValidateResponse(BaseModel):
    valid: bool
    error: Optional[str] = None


@router.get("/", response_model=Optional[LlmKeyResponse])
async def get_llm_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's LLM credential (key masked)."""
    cred = db.query(LlmCredential).filter(LlmCredential.user_id == current_user.id).first()
    if not cred:
        return None
    return {
        "provider": cred.provider,
        "key_last4": cred.key_last4,
        "model": cred.model,
        "created_at": cred.created_at.isoformat(),
        "last_verified_at": cred.last_verified_at.isoformat() if cred.last_verified_at else None,
        "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
    }


@router.put("/", response_model=LlmKeyResponse)
async def set_llm_key(
    data: LlmKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set or update LLM API key (encrypted at rest)."""
    if data.provider not in ("openai",):
        raise HTTPException(400, "Unsupported provider. Currently only 'openai' is supported.")
    if len(data.api_key) < 10:
        raise HTTPException(400, "Invalid API key")

    cred = db.query(LlmCredential).filter(LlmCredential.user_id == current_user.id).first()
    if not cred:
        cred = LlmCredential(user_id=current_user.id)
        db.add(cred)

    cred.provider = data.provider
    cred.encrypted_api_key = encrypt_value(data.api_key)
    cred.key_last4 = data.api_key[-4:]
    cred.model = data.model or "gpt-4o-mini"
    cred.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cred)

    return {
        "provider": cred.provider,
        "key_last4": cred.key_last4,
        "model": cred.model,
        "created_at": cred.created_at.isoformat(),
        "last_verified_at": cred.last_verified_at.isoformat() if cred.last_verified_at else None,
        "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
    }


@router.delete("/")
async def delete_llm_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove stored LLM API key."""
    cred = db.query(LlmCredential).filter(LlmCredential.user_id == current_user.id).first()
    if not cred:
        raise HTTPException(404, "No API key found")
    db.delete(cred)
    db.commit()
    return {"ok": True}


@router.post("/validate", response_model=LlmKeyValidateResponse)
async def validate_llm_key(
    data: LlmKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate an API key by making a minimal API call."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=data.api_key)
        client.models.list()

        # If validation passes and user has stored key, update last_verified_at
        cred = db.query(LlmCredential).filter(LlmCredential.user_id == current_user.id).first()
        if cred:
            cred.last_verified_at = datetime.utcnow()
            db.commit()

        return {"valid": True}
    except Exception as e:
        return {"valid": False, "error": str(e)}
