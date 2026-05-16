
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from core.database import get_db
from core.dependencies import require_roles
from core.email_service import EmailService

from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication
from models.Repayment.emi_scheduled import EMISchedule
from models.Repayment.payments import Payment_Transaction
from models.Repayment.ndc_generation import NoDueCertificate

router = APIRouter(prefix="/ndc", tags=["NDC Certificate"])


# =========================
# STYLES
# =========================
TITLE = ParagraphStyle(name="title", fontName="Helvetica-Bold", fontSize=14, alignment=TA_CENTER)
BODY = ParagraphStyle(name="body", fontName="Helvetica", fontSize=10, alignment=TA_LEFT)
LABEL = ParagraphStyle(name="label", fontName="Helvetica-Bold", fontSize=10)


# =========================
# MAIN API (FINAL)
# =========================
@router.get("/download")
async def download_ndc(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):

    # 🔐 Get user's CLOSED loan
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == current_user.id,
        LoanApplication.application_status == "CLOSED"
    ).first()

    if not loan:
        raise HTTPException(404, "No CLOSED loan found")

    application_id = loan.id

    # 🔐 Check EMIs paid
    unpaid = db.query(EMISchedule).filter(
        EMISchedule.application_id == application_id,
        EMISchedule.status != "PAID"
    ).first()

    if unpaid:
        raise HTTPException(400, "Loan not fully paid")

    # 📊 Payments
    payments = db.query(Payment_Transaction).filter(
        Payment_Transaction.application_id == application_id,
        Payment_Transaction.status == "SUCCESS"
    ).all()

    total_paid = sum(float(p.amount_paid or 0) for p in payments)

    closure_date = max(
        [p.created_at for p in payments],
        default=datetime.utcnow()
    )

    # 📄 PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []

    elements.append(Paragraph("NO DUE CERTIFICATE", TITLE))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        f"This is to certify that {current_user.name} has fully repaid the loan "
        f"(Application ID: {application_id}). No dues pending.",
        BODY
    ))

    elements.append(Spacer(1, 20))

    table = Table([
        ["Field", "Details"],
        ["Borrower", current_user.name],
        ["Application ID", str(application_id)],
        ["Total Paid", f"₹{round(total_paid, 2)}"],
        ["Status", "CLOSED"],
        ["Closure Date", closure_date.strftime("%Y-%m-%d")]
    ])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    # 📧 EMAIL (SAFE)
    if current_user.email:
        await EmailService.send_email_with_attachment(
            to_email=current_user.email,
            subject="No Due Certificate",
            body="Your NDC certificate is attached.",
            file_bytes=pdf_bytes,
            filename=f"ndc_{application_id}.pdf"
        )

    # 💾 Save record
    existing = db.query(NoDueCertificate).filter(
        NoDueCertificate.application_id == application_id
    ).first()

    if not existing:
        db.add(NoDueCertificate(
            application_id=application_id,
            pdf_url="/ndc/download"
        ))
        db.commit()

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ndc_{application_id}.pdf"}
    )

