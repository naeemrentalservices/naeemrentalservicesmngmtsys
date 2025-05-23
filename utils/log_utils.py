import datetime
from flask import request
from utils.sheets_utils import create_sheet_if_not_exists

def log_activity(service, spreadsheet_id, username, action, details, ip_address=None):
    """Log an activity to the ActivityLogs sheet."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip_address = ip_address or request.remote_addr if request else "N/A"
        
        # Ensure the ActivityLogs sheet exists
        create_sheet_if_not_exists(
            service, 
            spreadsheet_id, 
            "ActivityLogs", 
            ["Timestamp", "User", "Action", "Details", "IP Address"]
        )
        
        log_data = [
            timestamp,
            username,
            action,
            details,
            ip_address
        ]
        
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="ActivityLogs!A1",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [log_data]}
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False
