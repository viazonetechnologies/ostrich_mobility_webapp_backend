from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Simple CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Simple API"}

@app.post("/api/v1/notifications/send-to-customer/{customer_id}")
def send_notification(
    customer_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    send_via_email: bool = False,
    send_via_sms: bool = False
):
    return {"message": f"Notification sent to customer {customer_id}"}

@app.post("/api/v1/notifications/broadcast")
def broadcast(
    title: str,
    message: str,
    notification_type: str = "info",
    send_via_email: bool = False,
    send_via_sms: bool = False
):
    return {"message": "Broadcast sent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)