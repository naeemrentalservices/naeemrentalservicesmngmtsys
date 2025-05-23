from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
import io
import os

def initialize_drive_service():
    """Initialize and return a Google Drive service object."""
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    # Load credentials from service account file
    credentials = service_account.Credentials.from_service_account_file(
        'service_account.json', scopes=SCOPES)
    
    # Build the Drive service
    service = build('drive', 'v3', credentials=credentials)
    
    return service

def upload_file_to_drive(service, file_path, file_name, folder_id):
    """Upload a file to Google Drive and return its ID."""
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    return file.get('id')

def get_file_from_drive(service, file_id):
    """Get a file from Google Drive by ID and return its content."""
    request = service.files().get_media(fileId=file_id)
    
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    return file_content.getvalue()

def list_files_in_folder(service, folder_id):
    """List all files in a Google Drive folder."""
    query = f"'{folder_id}' in parents"
    
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType)'
    ).execute()
    
    return results.get('files', [])

def delete_file_from_drive(service, file_id):
    """Delete a file from Google Drive."""
    service.files().delete(fileId=file_id).execute()
    return True

def update_file_in_drive(service, file_id, file_path):
    """Update an existing file in Google Drive."""
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().update(fileId=file_id, media_body=media).execute()
    return file.get('id')

def create_folder_in_drive(service, folder_name, parent_id=None):
    """Create a folder in Google Drive."""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def share_file(service, file_id, email, role='reader'):
    """Share a file with a specific user."""
    batch = service.new_batch_http_request()
    
    user_permission = {
        'type': 'user',
        'role': role,
        'emailAddress': email
    }
    
    batch.add(service.permissions().create(
        fileId=file_id,
        body=user_permission,
        fields='id',
    ))
    
    batch.execute()
    return True
