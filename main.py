import os
import smtplib
from email.message import EmailMessage
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from schemas import Lead
from database import create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


# -------- Email utilities ---------

def get_sede_cc_email(sede: str) -> str | None:
    """Return CC email for a sede using environment variables.
    Expected env names:
    - SEDE_SAN_ISIDRO_EMAIL
    - SEDE_LA_MOLINA_EMAIL
    - SEDE_PUEBLO_LIBRE_EMAIL
    - SEDE_BRENA_EMAIL
    - SEDE_SAN_MIGUEL_EMAIL
    """
    key_map = {
        "San Isidro": "SEDE_SAN_ISIDRO_EMAIL",
        "La Molina": "SEDE_LA_MOLINA_EMAIL",
        "Pueblo Libre": "SEDE_PUEBLO_LIBRE_EMAIL",
        "Breña": "SEDE_BRENA_EMAIL",
        "San Miguel": "SEDE_SAN_MIGUEL_EMAIL",
    }
    env_key = key_map.get(sede)
    return os.getenv(env_key) if env_key else None


def send_email(subject: str, body: str, to_addrs: List[str], cc_addrs: List[str] | None = None) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "no-reply@localhost")

    if not smtp_host or not smtp_user or not smtp_pass:
        # Email not configured; skip silently but return False
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception:
        return False


@app.post("/api/leads")
def create_lead(lead: Lead):
    """Create a lead for Kids/Mini Kids summer courses, store it in DB and email notification."""
    try:
        # Validate via Pydantic (FastAPI also does this, but keep explicit for clarity)
        _ = Lead(**lead.model_dump())
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=str(ve))

    # Store in database
    try:
        lead_id = create_document("lead", lead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Prepare email
    sede_cc = get_sede_cc_email(lead.sede)
    to_addrs = [os.getenv("LEADS_TO", "cursos@acropolisperu.org")]
    cc_addrs = [sede_cc] if sede_cc else []

    subject = f"Nueva Acrópolis Lima - Lead Kids ({lead.program}) - {lead.sede}"
    body = (
        f"Nuevo lead recibido para Cursos de Verano Kids\n\n"
        f"Sede: {lead.sede}\n"
        f"Programa: {lead.program}\n"
        f"Cursos de interés: {', '.join(lead.courses) if lead.courses else 'N/A'}\n\n"
        f"Datos del padre/madre:\n"
        f"- Nombre: {lead.parent_name}\n"
        f"- Email: {lead.parent_email}\n"
        f"- Teléfono: {lead.parent_phone}\n\n"
        f"Datos del niño/niña:\n"
        f"- Nombre: {lead.child_name}\n"
        f"- Edad: {lead.child_age}\n\n"
        f"Mensaje: {lead.message or '—'}\n"
        f"Fuente: {lead.source or '—'}\n"
        f"ID: {lead_id}\n"
    )

    email_sent = send_email(subject, body, to_addrs, cc_addrs)

    return {"ok": True, "id": lead_id, "email_sent": email_sent}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
