from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime

def initialize_sheets_service():
    """Initialize and return a Google Sheets service object."""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    # Load credentials from service account file
    credentials = service_account.Credentials.from_service_account_file(
        'service_account.json', scopes=SCOPES)
    
    # Build the Sheets service
    service = build('sheets', 'v4', credentials=credentials)
    
    return service

def get_sheet_data(service, spreadsheet_id, sheet_name):
    """Get all data from a specific sheet in a spreadsheet."""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name
    ).execute()
    
    return result.get('values', [])

def append_sheet_data(service, spreadsheet_id, sheet_name, values):
    """Append data to a specific sheet in a spreadsheet."""
    body = {
        'values': values
    }
    
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption='RAW',
        body=body
    ).execute()
    
    return result

def update_sheet_data(service, spreadsheet_id, sheet_name, row_index, values):
    """Update a specific row in a sheet."""
    range_name = f"{sheet_name}!A{row_index}:{chr(65 + len(values) - 1)}{row_index}"
    
    body = {
        'values': [values]
    }
    
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    return result

def delete_sheet_row(service, spreadsheet_id, sheet_name, row_index):
    """Delete a specific row from a sheet."""
    # Get the sheet ID
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    sheet_id = None
    
    for sheet in sheets:
        if sheet['properties']['title'] == sheet_name:
            sheet_id = sheet['properties']['sheetId']
            break
    
    if not sheet_id:
        return False
    
    # Create delete request
    request = {
        'deleteDimension': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': row_index - 1,  # 0-based index
                'endIndex': row_index  # exclusive
            }
        }
    }
    
    # Execute the request
    body = {
        'requests': [request]
    }
    
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    
    return result

def create_sheet_if_not_exists(service, spreadsheet_id, sheet_name, headers=None):
    """Create a sheet in a spreadsheet if it doesn't exist."""
    try:
        # Check if the sheet already exists
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        
        # Check if the sheet already exists
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                # Sheet exists, check if it has headers
                if headers:
                    # Get the first row to check for headers
                    result = service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range=f"{sheet_name}!A1:Z1"
                    ).execute()
                    
                    values = result.get('values', [])
                    
                    # If no values or empty first row, add headers
                    if not values or not values[0]:
                        service.spreadsheets().values().update(
                            spreadsheetId=spreadsheet_id,
                            range=f"{sheet_name}!A1",
                            valueInputOption='RAW',
                            body={'values': [headers]}
                        ).execute()
                
                return True
        
        # Sheet doesn't exist, create it
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        # Add headers if provided
        if headers:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
        
        return True
    except Exception as e:
        print(f"Error creating sheet {sheet_name}: {e}")
        return False

def initialize_database_sheets(service, spreadsheet_id):
    """Initialize all required sheets for the application."""
    # Define sheets and their headers
    sheets = {
        "Users": ["Name", "Username", "Password", "Role"],
        "Customers": ["Name", "CNIC", "Phone", "Address", "ID Card Front", "ID Card Back", "Agreement", "Date Added"],
        "Products": ["Name", "Model", "Engine Number", "Chassis Number", "Market Value", "Description", "Images", "Date Added"],
        "Transactions": ["Transaction Name", "Description", "Amount", "Type", "Category", "Date"],
        "ActivityLogs": ["Timestamp", "User", "Action", "Details", "IP Address"]
    }
    
    # Create each sheet if it doesn't exist
    for sheet_name, headers in sheets.items():
        create_sheet_if_not_exists(service, spreadsheet_id, sheet_name, headers)
    
    return True
