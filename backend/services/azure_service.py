import os
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename
import uuid

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_foto_anak(file):
    """Upload foto anak ke Azure Blob Storage, return URL publik"""
    
    connection_string = os.environ.get('AZURE_CONNECTION_STRING')
    container_name = os.environ.get('AZURE_CONTAINER_NAME', 'foto-anak')
    
    if not connection_string:
        raise Exception("Azure connection string tidak ditemukan")
    
    if not allowed_file(file.filename):
        raise Exception("Format file tidak didukung. Gunakan PNG, JPG, atau JPEG")
    
    # Nama file unik pakai UUID
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Upload ke Azure
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=filename
    )
    
    file.seek(0)
    blob_client.upload_blob(file.read(), overwrite=True)
    
    # Return URL publik
    url = f"https://tumbuhcerahstorage.blob.core.windows.net/{container_name}/{filename}"
    return url