import re
import uuid
import os
import cloudinary.uploader

from fastapi import UploadFile, HTTPException

# =====================================================
# CONFIG
# =====================================================
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

ALLOWED_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/pdf",
]


# =====================================================
# CLEAN CATEGORY NAME
# =====================================================
def clean_folder_name(value: str) -> str:
    """
    Converts: Login Issue -> LOGIN_ISSUE
    """
    value = value.strip().upper()
    value = re.sub(r"[^A-Z0-9]+", "_", value)
    return value.strip("_")


# =====================================================
# MAIN UPLOAD FUNCTION
# =====================================================
async def upload_support_attachment(
    attachment: UploadFile,
    category: str,
    user_id: int,
    complaint_id: int,
) -> str:

    # Read file
    content = await attachment.read()

    # ===============================
    # FILE SIZE VALIDATION
    # ===============================
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Attachment size must be <= 2 MB"
        )

    # ===============================
    # FILE TYPE VALIDATION
    # ===============================
    if attachment.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, PDF allowed"
        )

    # ===============================
    # SAFE FILENAME
    # ===============================
    original_filename = os.path.basename(attachment.filename)

    # Unique filename to avoid collisions
    unique_filename = f"{uuid.uuid4()}_{original_filename}"

    # ===============================
    # CLEAN CATEGORY
    # ===============================
    folder_category = clean_folder_name(category)

    # ===============================
    # FINAL FOLDER STRUCTURE
    # ===============================
    folder_path = (
        f"support_attachment_files/"
        f"{folder_category}/"
        f"user_{user_id}/"
        f"complaint_{complaint_id}"
    )

    try:
        result = cloudinary.uploader.upload(
            content,
            folder=folder_path,
            resource_type="auto",
            public_id=unique_filename,
            overwrite=False,
        )

        return result.get("secure_url")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cloudinary upload failed: {str(e)}"
        )