import cloudinary
import cloudinary.uploader
import os
from core.config import settings

def upload_image(file):
    return cloudinary.uploader.upload(file)

def delete_image(public_id):
    return cloudinary.uploader.destroy(public_id)