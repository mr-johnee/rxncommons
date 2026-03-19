from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, datasets, files, interactions, stats, versions, admin, notifications, suggestions

api_router = APIRouter()

# Register routes with more specific paths first!
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(versions.router, prefix="/datasets/{dataset_id}/versions", tags=["versions"])
api_router.include_router(files.router, prefix="/datasets/{dataset_id}/files", tags=["files"])
api_router.include_router(interactions.router, prefix="/datasets", tags=["interactions"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])

@api_router.get("/health")
def health_check():
    return {"status": "ok", "message": "RxnCommons API is running"}

api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(suggestions.router, prefix="/suggestions", tags=["suggestions"])

