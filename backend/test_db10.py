from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# wait, I don't have auth token easily.
# Let's just create a mock user and override get_current_admin dependency
from app.api.deps import get_current_admin
from app.models.user import User

def mock_get_admin():
    from app.core.database import SessionLocal
    db = SessionLocal()
    return db.query(User).filter(User.role == 'admin').first()

app.dependency_overrides[get_current_admin] = mock_get_admin

response = client.get("/api/v1/admin/review-requests")
print(response.json()['items'][0] if response.json()['items'] else 'No items')
