
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import uuid
import os

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication
from models.Repayment.emi_scheduled import EMISchedule
from core.email_service import EmailService

router = APIRouter(prefix="/emi-pdf", tags=["EMI Schedule"])


@router.get("/download")
async def download_emi_pdf(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):

    # =====================================================
    # 🔒 GET ACTIVE LOAN (SAFE)
    # =====================================================
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == current_user.id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        raise HTTPException(404, "No ACTIVE loan found")

    # =====================================================
    # 📊 FETCH EMI DATA
    # =====================================================
    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id
    ).order_by(EMISchedule.emi_number).all()

    if not emis:
        raise HTTPException(404, "No EMI schedule found")

    # =====================================================
    # 📄 CREATE UNIQUE FILE
    # =====================================================
    file_path = f"EMI_{loan.id}_{uuid.uuid4().hex}.pdf"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=25,
        bottomMargin=25
    )

    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("EMI Repayment Schedule", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Loan ID: {loan.id}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    table_data = [[
        "EMI No", "Due Date", "Principal", "Interest", "GST", "Total EMI"
    ]]

    total = 0

    for emi in emis:
        table_data.append([
            str(emi.emi_number),
            emi.due_date.strftime("%d-%m-%Y"),
            f"{float(emi.principal_component):,.2f}",
            f"{float(emi.interest_component):,.2f}",
            f"{float(emi.gst_amount):,.2f}",
            f"{float(emi.emi_amount):,.2f}"
        ])
        total += float(emi.emi_amount)

    table_data.append(["", "", "", "", "Total", f"{total:,.2f}"])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ]))

    elements.append(table)
    doc.build(elements)

    # =====================================================
    # 📧 EMAIL SEND (SAFE)
    # =====================================================
    if current_user.email:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        await EmailService.send_email_with_attachment(
            to_email=current_user.email,
            subject="EMI Schedule",
            body="Please find your EMI schedule attached.",
            file_bytes=file_bytes,
            filename=f"EMI_Schedule_{loan.id}.pdf"
        )

    # =====================================================
    # 🧹 CLEANUP FILE
    # =====================================================
    background_tasks.add_task(os.remove, file_path)

    return FileResponse(
        path=file_path,
        filename=f"EMI_Schedule_{loan.id}.pdf",
        media_type="application/pdf"
    )

