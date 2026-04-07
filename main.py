# main.py
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
from models.Support import chat, complaint, grievance
from models.Esign import agreements, esign_session, signed_documents, audit_logs
from services.Auth.otp_cleanup import cleanup_otps
from core.database import Base
from core.database import engine, SessionLocal
from core.seed import create_default_super_admin
from core.config import settings

# Importing routers

from routers.Auth import lender
from routers.Auth import superadmin_access
from routers.Auth import login_SL
from routers.Auth import user_register
from routers.Eligibility.credit_route import router as credit_router
from routers.Eligibility.eligibility_route import router as eligibility_router
from routers.Eligibility.eligibility_result import router as eligibility_result_router
from routers.Eligibility.loan_calculator_route import router as loan_calculator_router
from routers.Eligibility.loan_calculator_result import router as loan_router
from routers.Loan_application.loan_eligibility_router import router as loan_eligibility_router
from routers.Loan_application.loan_application_router import router as loan_application_router
from routers.Loan_application.loan_application_purpose_router import router as loan_application_purpose_router
from routers.Loan_application.loan_application_reference_router import router as loan_application_reference_router
from routers.Loan_application.reference_otp_router import router as reference_otp_router
from routers.Loan_application.loan_application_summary_router import router as loan_application_summary_router
from routers.Loan_application.loan_application_declaration_router import router as loan_application_declaration_router
from routers.Loan_application.lender_router import router as lender_router
from routers.Loan_application.loan_disbursement_router import router as loan_disbursement_router
from routers.Support import chat, complaint, contact, faq, grievance
from routers.Support.faq import router as faq_router
from routers.Support.chat import router as chat_router
from routers.Support.complaint import router as complaint_router
from routers.Support.contact import router as contact_router
from routers.Support.grievance import router as grievance_router
from routers.Esign.esign_router import router as esign_router
from routers.Esign.agreement_router import router as agreement_router
from routers.Esign.disbursement_router import router as disbursement_router
from routers.Profile_KYC.profile_router import router as profile_router
from routers.Profile_KYC.pan_router import router as pan_router
from routers.Profile_KYC.aadhaar_router import router as aadhaar_router
from routers.Profile_KYC.bank_router import router as bank_router
from routers.Profile_KYC.document_router import router as document_router
from routers.Profile_KYC.admin_router import router as admin_router
from services.Profile_KYC.auto_cleanup import AutoCleanup
from routers.Consent.consent_routers import router as consent_router
from routers.Consent.legal_routers import router as legal_router
from routers.Tracking.tracking_router import router as tracking_router
from routers.Tracking.reupload_router import router as reupload_router
from routers.Tracking.notifications_router import router as notifications_router
from routers.Tracking.nbfc_webhook_router import router as nbfc_webhook_router
from routers.Tracking.internal_status_router import router as internal_status_router
from routers.Settings.profile_router import router as settings_profile_router
from routers.Settings.settings_router import router as settings_router



print("DB URL USED BY APP:", settings.DATABASE_URL)
Base.metadata.create_all(bind=engine)
auto_cleanup = AutoCleanup(interval_hours=24)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine, checkfirst=True)

        # 🔍 DEBUG PRINTS (ADD HERE)
    print("NAME:", settings.SUPER_ADMIN_NAME)
    print("MOBILE:", settings.SUPER_ADMIN_MOBILE)
    print("PASSWORD:", settings.SUPER_ADMIN_PASSWORD)

    upload_dirs = ["uploads","uploads/aadhaar","uploads/pan","uploads/salary_slips","uploads/bank_statements"]
    for dir_path in upload_dirs:
        os.makedirs(dir_path, exist_ok=True)

    auto_cleanup.start()
    print("Auto cleanup service started")

    yield

    auto_cleanup.stop()
    print("Auto cleanup service stopped")


app = FastAPI(title="Loan Service Platform - OTP and Session Auth API",lifespan=lifespan)

@app.on_event("startup")
def startup():
    print("👉 Calling create_default_super_admin()")

db = SessionLocal()
try:
    result = create_default_super_admin(
        db,
        settings.SUPER_ADMIN_NAME,
        settings.SUPER_ADMIN_MOBILE,
        settings.SUPER_ADMIN_PASSWORD,
        settings.SUPER_ADMIN_DEVICE_ID,
    )
    print("👉 Result:", result)
finally:
    db.close()


#Auth Routers

app.include_router(login_SL.router)
app.include_router(user_register.router)
app.include_router(lender.router)
app.include_router(superadmin_access.router)

#Profile and KYC Routers
app.include_router(profile_router)
app.include_router(pan_router)
app.include_router(aadhaar_router)
app.include_router(bank_router)
app.include_router(document_router)
app.include_router(admin_router)

# Consent and Legal Routers
app.include_router(consent_router)
app.include_router(legal_router)

# Eligibility and Credit Profile Routers
app.include_router(credit_router,tags=["Credit Profile"])
app.include_router(eligibility_router, tags=["Loan Eligibility"])
app.include_router(eligibility_result_router, tags=["Loan Eligibility"])
app.include_router(loan_calculator_router,  tags=["Loan Calculator"])
app.include_router(loan_router,tags=["Loan Calculator"])

#Loan Application Routers
# app.include_router(loan_eligibility_router)

app.include_router(loan_application_router)
app.include_router(loan_application_purpose_router)
app.include_router(loan_application_reference_router)   
app.include_router(reference_otp_router)
app.include_router(loan_application_declaration_router)

# app.include_router(loan_application_summary_router)
app.include_router(lender_router)
app.include_router(loan_disbursement_router)

#Tracking Routers
app.include_router(tracking_router)
app.include_router(reupload_router)
app.include_router(notifications_router)
app.include_router(nbfc_webhook_router)
app.include_router(internal_status_router)



#Support Routers
app.include_router(faq_router)
app.include_router(chat_router)
app.include_router(complaint_router)
app.include_router(contact_router)
app.include_router(grievance_router)

#Esign Routers
app.include_router(agreement_router)
app.include_router(esign_router)
app.include_router(disbursement_router)

#Settings Routers
app.include_router(settings_profile_router)
app.include_router(settings_router)

# OTP Cleanup Task
async def otp_cleanup_loop():
    while True:
        db = SessionLocal()
        try:
            cleanup_otps(db)
        finally:
            db.close()
        await asyncio.sleep(300)  # every 5 minutes
 
 
@app.on_event("startup")
async def start_cleanup():
    asyncio.create_task(otp_cleanup_loop())



