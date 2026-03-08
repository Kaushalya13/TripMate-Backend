from fastapi import APIRouter, Depends, HTTPException
from middleware import admin_only
from lib.db import supabase

router = APIRouter(prefix="/api/auth", tags=["Auth & User Management"])

@router.get("/profile/{user_id}")
def get_profile(user_id: str):
    res = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    return res.data

@router.get("/admin/users")
def get_all_users(admin_id: str = Depends(admin_only)):
    res = supabase.table("profiles").select("*").execute()
    return res.data

@router.delete("/admin/user/{target_id}")
def delete_user(target_id: str, admin_id: str = Depends(admin_only)):
    supabase.table("profiles").delete().eq("id", target_id).execute()
    return {"message": "User deleted"}