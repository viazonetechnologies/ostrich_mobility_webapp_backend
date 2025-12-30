from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

app = FastAPI()

# Allow your Vercel domain
allowed_origins = [
    "http://localhost:3000",
    "https://ostrich-mobility-webapp-frontend-iw0b0ulsl.vercel.app",
    "https://ostrich-mobility-webapp-frontend-ez5dm6l81.vercel.app",
    "https://*.vercel.app",
    os.getenv("FRONTEND_URL", "")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/notifications/broadcast")
def broadcast(
    title: str,
    message: str,
    notification_type: str = "info",
    send_via_email: bool = False,
    send_via_sms: bool = False
):
    return {"message": f"Broadcast sent: {title}"}

@app.post("/api/v1/notifications/send-to-customer/{customer_id}")
def send_to_customer(
    customer_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    send_via_email: bool = False,
    send_via_sms: bool = False
):
    return {"message": f"Sent to customer {customer_id}: {title}"}

@app.get("/api/v1/notifications/")
def get_notifications():
    return []

@app.get("/api/v1/customers/")
def get_customers():
    return [{"id": 1, "contact_person": "Test Customer", "email": "test@test.com", "phone": "123456789"}]

@app.get("/api/v1/users/")
def get_users():
    return [{"id": 1, "first_name": "Test", "last_name": "User", "email": "user@test.com"}]

@app.get("/")
def root():
    return {"message": "API Working"}



if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)