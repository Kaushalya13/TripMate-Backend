from fastapi import Request, HTTPException
from lib.db import supabase

async def admin_only(request: Request):
    # Expects X-User-Id header from Frontend
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    res = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
    if not res.data or res.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user_id