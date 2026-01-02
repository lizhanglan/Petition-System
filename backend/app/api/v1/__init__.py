from fastapi import APIRouter
from app.api.v1.endpoints import auth, files, documents, templates, versions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(files.router, prefix="/files", tags=["文件管理"])
api_router.include_router(documents.router, prefix="/documents", tags=["文书管理"])
api_router.include_router(templates.router, prefix="/templates", tags=["模板管理"])
api_router.include_router(versions.router, prefix="/versions", tags=["版本管理"])
