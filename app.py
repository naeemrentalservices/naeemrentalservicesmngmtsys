from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import datetime
import tempfile
from functools import wraps

# Import utility modules
from utils.sheets_utils import (
    initialize_sheets_service, 
    get_sheet_data, 
    append_sheet_data, 
    update_sheet_data, 
    delete_sheet_row,
    create_sheet_if_not_exists,
    initialize_database_sheets
)
from utils.drive_utils import (
    initialize_drive_service, 
    upload_file_to_drive
)
from utils.auth_utils import role_required
from utils.log_utils import log_activity

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rental-management-secret-key-2024')
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Constants - Your Google IDs
SPREADSHEET_ID = "19z40iF2KQeLngSJWVWxLYPQ9hrZBZRATcc-F-4uo_8w"
AGREEMENT_DOC_ID = "18iK2psouFM-WWzeYKgKIUW0V7eIF5wfq"
FOLDER_ID = "1EeUnMs2olg06iHu3TzipYzdZWsXdhQQW"

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, name, role):
        self.id = id
        self.username = username
        self.name = name
        self.role = role

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        sheets_service = initialize_sheets_service()
        users = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
        
        for i, user in enumerate(users):
            if i > 0 and len(user) > 1 and user[1] == user_id:  # Skip header row
                return User(user[1], user[1], user[0], user[3] if len(user) > 3 else "Employee")
    except Exception as e:
        print(f"Error loading user: {e}")
    
    return None

# Initialize database and create default admin user
def initialize_database():
    try:
        sheets_service = initialize_sheets_service()
        initialize_database_sheets(sheets_service, SPREADSHEET_ID)
        
        # Check if any users exist
        users = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
        
        # If no users exist (only header row), create default admin
        if len(users) <= 1:
            print("No users found. Creating default admin user...")
            default_admin = [
                "Administrator",  # Name
                "admin",          # Username
                generate_password_hash("admin123"),  # Password hash
                "Owner"           # Role
            ]
            append_sheet_data(sheets_service, SPREADSHEET_ID, "Users", [default_admin])
            print("Default admin user created:")
            print("Username: admin")
            print("Password: admin123")
            print("Please change this password after first login!")
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Use this pattern instead of before_first_request
with app.app_context():
    initialize_database()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            sheets_service = initialize_sheets_service()
            users = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
            
            for i, user in enumerate(users):
                if i > 0 and len(user) > 2 and user[1] == username:  # Skip header row
                    if check_password_hash(user[2], password):
                        user_obj = User(user[1], user[1], user[0], user[3] if len(user) > 3 else "Employee")
                        login_user(user_obj)
                        
                        # Log activity
                        log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Login", "User logged in")
                        
                        next_page = request.args.get('next')
                        return redirect(next_page or url_for('dashboard'))
                    else:
                        flash('Invalid username or password', 'error')
                        return render_template('login.html')
            
            flash('Invalid username or password', 'error')
        except Exception as e:
            flash(f'Error connecting to database: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    try:
        sheets_service = initialize_sheets_service()
        log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Logout", "User logged out")
    except Exception as e:
        print(f"Error logging logout: {e}")
    
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('profile'))
        
        sheets_service = initialize_sheets_service()
        users = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
        
        # Find current user
        for i, user in enumerate(users):
            if i > 0 and len(user) > 1 and user[1] == current_user.username:
                if check_password_hash(user[2], current_password):
                    # Update password
                    updated_user = [user[0], user[1], generate_password_hash(new_password), user[3]]
                    update_sheet_data(sheets_service, SPREADSHEET_ID, "Users", i + 1, updated_user)
                    
                    # Log activity
                    log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Change Password", "Password changed successfully")
                    
                    flash('Password changed successfully', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Current password is incorrect', 'error')
                    return redirect(url_for('profile'))
        
        flash('User not found', 'error')
        return redirect(url_for('profile'))
        
    except Exception as e:
        flash(f'Error changing password: {str(e)}', 'error')
        return redirect(url_for('profile'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        sheets_service = initialize_sheets_service()
        
        # Get summary data
        customers = get_sheet_data(sheets_service, SPREADSHEET_ID, "Customers")
        products = get_sheet_data(sheets_service, SPREADSHEET_ID, "Products")
        accounts = get_sheet_data(sheets_service, SPREADSHEET_ID, "Transactions")
        logs = get_sheet_data(sheets_service, SPREADSHEET_ID, "ActivityLogs")
        
        # Calculate financial summaries
        total_earnings = 0
        total_expenditures = 0
        
        # Skip header row and process transactions
        if len(accounts) > 1:
            for account in accounts[1:]:
                if len(account) > 3:
                    try:
                        amount = float(account[2])  # Amount is in column 2
                        if account[3] == "Income":
                            total_earnings += amount
                        elif account[3] == "Expense":
                            total_expenditures += amount
                    except (ValueError, TypeError):
                        pass
        
        net_balance = total_earnings - total_expenditures
        
        # Get last 5 activities (skip header row)
        recent_activities = []
        if len(logs) > 1:
            recent_activities = logs[-6:-1] if len(logs) > 6 else logs[1:]
            recent_activities.reverse()  # Show most recent first
        
        # Prepare chart data (dummy data for now since we don't have historical data)
        chart_labels = []
        income_data = []
        expense_data = []
        
        # Generate last 6 months for chart
        import calendar
        current_date = datetime.datetime.now()
        for i in range(5, -1, -1):
            month_date = current_date.replace(day=1) - datetime.timedelta(days=i*30)
            month_label = f"{month_date.year}-{month_date.month:02d}"
            chart_labels.append(month_label)
            
            # For now, add dummy data - you can enhance this later with actual monthly data
            if i == 0:  # Current month
                income_data.append(total_earnings)
                expense_data.append(total_expenditures)
            else:
                income_data.append(0)
                expense_data.append(0)
        
        return render_template(
            'dashboard.html',
            total_customers=len(customers) - 1 if len(customers) > 1 else 0,
            total_products=len(products) - 1 if len(products) > 1 else 0,
            total_earnings=total_earnings,
            total_expenditures=total_expenditures,
            net_balance=net_balance,
            recent_activities=recent_activities,
            chart_labels=chart_labels,
            income_data=income_data,
            expense_data=expense_data
        )
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', 
                             total_customers=0, total_products=0, 
                             total_earnings=0, total_expenditures=0, 
                             net_balance=0, recent_activities=[],
                             chart_labels=[], income_data=[], expense_data=[])

@app.route('/customers')
@login_required
def customers():
    try:
        sheets_service = initialize_sheets_service()
        customers_data = get_sheet_data(sheets_service, SPREADSHEET_ID, "Customers")
        
        # Skip header row
        customers_data = customers_data[1:] if len(customers_data) > 1 else []
        
        return render_template('customers.html', customers=customers_data)
    except Exception as e:
        flash(f'Error loading customers: {str(e)}', 'error')
        return render_template('customers.html', customers=[])

@app.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            cnic = request.form.get('cnic')
            phone = request.form.get('phone')
            address = request.form.get('address', '')
            
            # Initialize services
            drive_service = initialize_drive_service()
            sheets_service = initialize_sheets_service()
            
            # Handle file uploads
            id_front_id = ""
            id_back_id = ""
            
            # Handle ID card front upload
            id_front_file = request.files.get('id_front')
            if id_front_file and id_front_file.filename:
                filename = secure_filename(f"{name}_{cnic}_id_front_{id_front_file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                id_front_file.save(filepath)
                
                # Upload to Google Drive
                id_front_id = upload_file_to_drive(drive_service, filepath, filename, FOLDER_ID)
                
                # Clean up local file
                os.remove(filepath)
            
            # Handle ID card back upload
            id_back_file = request.files.get('id_back')
            if id_back_file and id_back_file.filename:
                filename = secure_filename(f"{name}_{cnic}_id_back_{id_back_file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                id_back_file.save(filepath)
                
                # Upload to Google Drive
                id_back_id = upload_file_to_drive(drive_service, filepath, filename, FOLDER_ID)
                
                # Clean up local file
                os.remove(filepath)
            
            # Add customer to Google Sheets
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            customer_data = [[name, cnic, phone, address, id_front_id, id_back_id, today]]
            append_sheet_data(sheets_service, SPREADSHEET_ID, "Customers", customer_data)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Add Customer", f"Added customer: {name}")
            
            flash('Customer added successfully', 'success')
            return redirect(url_for('customers'))
            
        except Exception as e:
            flash(f'Error adding customer: {str(e)}', 'error')
    
    return render_template('add_customer.html')

@app.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    try:
        sheets_service = initialize_sheets_service()
        customers = get_sheet_data(sheets_service, SPREADSHEET_ID, "Customers")
        
        # Skip header row and adjust index
        if customer_id >= len(customers) - 1 or customer_id < 0:
            flash('Customer not found', 'error')
            return redirect(url_for('customers'))
        
        customer = customers[customer_id + 1]  # +1 to account for header row
        
        if request.method == 'POST':
            name = request.form.get('name')
            cnic = request.form.get('cnic')
            phone = request.form.get('phone')
            address = request.form.get('address', '')
            
            # Initialize services
            drive_service = initialize_drive_service()
            
            # Handle file uploads (keep existing if no new file)
            id_front_id = customer[4] if len(customer) > 4 else ""
            id_back_id = customer[5] if len(customer) > 5 else ""
            
            # Handle ID card front upload
            id_front_file = request.files.get('id_front')
            if id_front_file and id_front_file.filename:
                filename = secure_filename(f"{name}_{cnic}_id_front_{id_front_file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                id_front_file.save(filepath)
                
                # Upload to Google Drive
                id_front_id = upload_file_to_drive(drive_service, filepath, filename, FOLDER_ID)
                
                # Clean up local file
                os.remove(filepath)
            
            # Handle ID card back upload
            id_back_file = request.files.get('id_back')
            if id_back_file and id_back_file.filename:
                filename = secure_filename(f"{name}_{cnic}_id_back_{id_back_file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                id_back_file.save(filepath)
                
                # Upload to Google Drive
                id_back_id = upload_file_to_drive(drive_service, filepath, filename, FOLDER_ID)
                
                # Clean up local file
                os.remove(filepath)
            
            # Update customer in Google Sheets
            date_added = customer[6] if len(customer) > 6 else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            updated_customer = [name, cnic, phone, address, id_front_id, id_back_id, date_added]
            update_sheet_data(sheets_service, SPREADSHEET_ID, "Customers", customer_id + 2, updated_customer)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Edit Customer", f"Updated customer: {name}")
            
            flash('Customer updated successfully', 'success')
            return redirect(url_for('customers'))
        
        return render_template('edit_customer.html', customer=customer, customer_id=customer_id)
        
    except Exception as e:
        flash(f'Error editing customer: {str(e)}', 'error')
        return redirect(url_for('customers'))

@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
@role_required(['Owner'])
def delete_customer(customer_id):
    try:
        sheets_service = initialize_sheets_service()
        customers = get_sheet_data(sheets_service, SPREADSHEET_ID, "Customers")
        
        # Skip header row and adjust index
        if customer_id >= len(customers) - 1 or customer_id < 0:
            flash('Customer not found', 'error')
            return redirect(url_for('customers'))
        
        customer = customers[customer_id + 1]  # +1 to account for header row
        
        # Delete customer from Google Sheets
        delete_sheet_row(sheets_service, SPREADSHEET_ID, "Customers", customer_id + 2)
        
        # Log activity
        log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Delete Customer", f"Deleted customer: {customer[0]}")
        
        flash('Customer deleted successfully', 'success')
        
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'error')
    
    return redirect(url_for('customers'))

@app.route('/products')
@login_required
def products():
    try:
        sheets_service = initialize_sheets_service()
        products_data = get_sheet_data(sheets_service, SPREADSHEET_ID, "Products")
        
        # Skip header row
        products_data = products_data[1:] if len(products_data) > 1 else []
        
        return render_template('products.html', products=products_data)
    except Exception as e:
        flash(f'Error loading products: {str(e)}', 'error')
        return render_template('products.html', products=[])

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            model = request.form.get('model')
            engine_number = request.form.get('engine_number')
            chassis_number = request.form.get('chassis_number')
            market_value = request.form.get('market_value')
            description = request.form.get('description', '')
            
            # Initialize services
            drive_service = initialize_drive_service()
            sheets_service = initialize_sheets_service()
            
            # Handle product images upload
            image_ids = []
            if 'images' in request.files:
                images = request.files.getlist('images')
                for i, image_file in enumerate(images):
                    if image_file and image_file.filename:
                        filename = secure_filename(f"{name}_{engine_number}_image_{i+1}_{image_file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        image_file.save(filepath)
                        
                        # Upload to Google Drive
                        image_id = upload_file_to_drive(drive_service, filepath, filename, FOLDER_ID)
                        image_ids.append(image_id)
                        
                        # Clean up local file
                        os.remove(filepath)
            
            # Add product to Google Sheets
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            product_data = [[name, model, engine_number, chassis_number, market_value, description, ",".join(image_ids), today]]
            append_sheet_data(sheets_service, SPREADSHEET_ID, "Products", product_data)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Add Product", f"Added product: {name}")
            
            flash('Product added successfully', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'error')
    
    return render_template('add_product.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    try:
        sheets_service = initialize_sheets_service()
        products = get_sheet_data(sheets_service, SPREADSHEET_ID, "Products")
        
        # Skip header row and adjust index
        if product_id >= len(products) - 1 or product_id < 0:
            flash('Product not found', 'error')
            return redirect(url_for('products'))
        
        product = products[product_id + 1]  # +1 to account for header row
        
        if request.method == 'POST':
            name = request.form.get('name')
            model = request.form.get('model')
            engine_number = request.form.get('engine_number')
            chassis_number = request.form.get('chassis_number')
            market_value = request.form.get('market_value')
            description = request.form.get('description', '')
            
            # Initialize services
            drive_service = initialize_drive_service()
            
            # Handle product images upload
            existing_image_ids = product[6].split(',') if len(product) > 6 and product[6] else []
            new_image_ids = []
            
            if 'images' in request.files:
                images = request.files.getlist('images')
                for i, image_file in enumerate(images):
                    if image_file and image_file.filename:
                        filename = secure_filename(f"{name}_{engine_number}_image_{len(existing_image_ids)+i+1}_{image_file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        image_file.save(filepath)
                        
                        # Upload to Google Drive
                        image_id = upload_file_to_drive(drive_service, filepath, filename, FOLDER_ID)
                        new_image_ids.append(image_id)
                        
                        # Clean up local file
                        os.remove(filepath)
            
            # Combine existing and new image IDs
            all_image_ids = existing_image_ids + new_image_ids
            
            # Update product in Google Sheets
            date_added = product[7] if len(product) > 7 else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_product = [name, model, engine_number, chassis_number, market_value, description, ",".join(all_image_ids), date_added]
            update_sheet_data(sheets_service, SPREADSHEET_ID, "Products", product_id + 2, updated_product)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Edit Product", f"Updated product: {name}")
            
            flash('Product updated successfully', 'success')
            return redirect(url_for('products'))
        
        return render_template('edit_product.html', product=product, product_id=product_id)
        
    except Exception as e:
        flash(f'Error editing product: {str(e)}', 'error')
        return redirect(url_for('products'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
@role_required(['Owner'])
def delete_product(product_id):
    try:
        sheets_service = initialize_sheets_service()
        products = get_sheet_data(sheets_service, SPREADSHEET_ID, "Products")
        
        # Skip header row and adjust index
        if product_id >= len(products) - 1 or product_id < 0:
            flash('Product not found', 'error')
            return redirect(url_for('products'))
        
        product = products[product_id + 1]  # +1 to account for header row
        
        # Delete product from Google Sheets
        delete_sheet_row(sheets_service, SPREADSHEET_ID, "Products", product_id + 2)
        
        # Log activity
        log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Delete Product", f"Deleted product: {product[0]}")
        
        flash('Product deleted successfully', 'success')
        
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('products'))

@app.route('/accounts')
@login_required
def accounts():
    try:
        sheets_service = initialize_sheets_service()
        accounts_data = get_sheet_data(sheets_service, SPREADSHEET_ID, "Transactions")
        
        # Skip header row
        accounts_data = accounts_data[1:] if len(accounts_data) > 1 else []
        
        # Calculate totals
        total_earnings = 0
        total_expenditures = 0
        
        for account in accounts_data:
            if len(account) > 3:
                try:
                    amount = float(account[2])  # Amount is in column 2
                    if account[3] == "Income":
                        total_earnings += amount
                    elif account[3] == "Expense":
                        total_expenditures += amount
                except (ValueError, TypeError):
                    pass
        
        net_balance = total_earnings - total_expenditures
        
        return render_template(
            'accounts.html', 
            transactions=accounts_data,
            total_earnings=total_earnings,
            total_expenditures=total_expenditures,
            net_balance=net_balance
        )
    except Exception as e:
        flash(f'Error loading accounts: {str(e)}', 'error')
        return render_template('accounts.html', transactions=[], 
                             total_earnings=0, total_expenditures=0, net_balance=0)

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            transaction_name = request.form.get('transaction_name')
            description = request.form.get('description', '')
            amount = request.form.get('amount')
            transaction_type = request.form.get('transaction_type')
            category = request.form.get('category', '')
            
            # Initialize services
            sheets_service = initialize_sheets_service()
            
            # Add transaction to Google Sheets
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            transaction_data = [[transaction_name, description, amount, transaction_type, category, today]]
            append_sheet_data(sheets_service, SPREADSHEET_ID, "Transactions", transaction_data)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Add Transaction", f"Added transaction: {transaction_name}")
            
            flash('Transaction added successfully', 'success')
            return redirect(url_for('accounts'))
            
        except Exception as e:
            flash(f'Error adding transaction: {str(e)}', 'error')
    
    return render_template('add_transaction.html')

@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    try:
        sheets_service = initialize_sheets_service()
        transactions = get_sheet_data(sheets_service, SPREADSHEET_ID, "Transactions")
        
        # Skip header row and adjust index
        if transaction_id >= len(transactions) - 1 or transaction_id < 0:
            flash('Transaction not found', 'error')
            return redirect(url_for('accounts'))
        
        transaction = transactions[transaction_id + 1]  # +1 to account for header row
        
        if request.method == 'POST':
            transaction_name = request.form.get('transaction_name')
            description = request.form.get('description', '')
            amount = request.form.get('amount')
            transaction_type = request.form.get('transaction_type')
            category = request.form.get('category', '')
            
            # Update transaction in Google Sheets
            date = transaction[5] if len(transaction) > 5 else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_transaction = [transaction_name, description, amount, transaction_type, category, date]
            update_sheet_data(sheets_service, SPREADSHEET_ID, "Transactions", transaction_id + 2, updated_transaction)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Edit Transaction", f"Updated transaction: {transaction_name}")
            
            flash('Transaction updated successfully', 'success')
            return redirect(url_for('accounts'))
        
        return render_template('edit_transaction.html', transaction=transaction, transaction_id=transaction_id)
        
    except Exception as e:
        flash(f'Error editing transaction: {str(e)}', 'error')
        return redirect(url_for('accounts'))

@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
@role_required(['Owner'])
def delete_transaction(transaction_id):
    try:
        sheets_service = initialize_sheets_service()
        transactions = get_sheet_data(sheets_service, SPREADSHEET_ID, "Transactions")
        
        # Skip header row and adjust index
        if transaction_id >= len(transactions) - 1 or transaction_id < 0:
            flash('Transaction not found', 'error')
            return redirect(url_for('accounts'))
        
        transaction = transactions[transaction_id + 1]  # +1 to account for header row
        
        # Delete transaction from Google Sheets
        delete_sheet_row(sheets_service, SPREADSHEET_ID, "Transactions", transaction_id + 2)
        
        # Log activity
        log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Delete Transaction", f"Deleted transaction: {transaction[0]}")
        
        flash('Transaction deleted successfully', 'success')
        
    except Exception as e:
        flash(f'Error deleting transaction: {str(e)}', 'error')
    
    return redirect(url_for('accounts'))

@app.route('/agreement')
@login_required
def agreement():
    return render_template('agreement.html', doc_id=AGREEMENT_DOC_ID)

@app.route('/inquiries')
@login_required
def inquiries():
    return render_template('inquiries.html')

@app.route('/activity_logs')
@login_required
@role_required(['Owner'])
def activity_logs():
    try:
        sheets_service = initialize_sheets_service()
        logs_data = get_sheet_data(sheets_service, SPREADSHEET_ID, "ActivityLogs")
        
        # Skip header row and reverse to show most recent first
        logs_data = logs_data[1:] if len(logs_data) > 1 else []
        logs_data.reverse()
        
        return render_template('activity_logs.html', logs=logs_data)
    except Exception as e:
        flash(f'Error loading activity logs: {str(e)}', 'error')
        return render_template('activity_logs.html', logs=[])

@app.route('/users')
@login_required
@role_required(['Owner'])
def users():
    try:
        sheets_service = initialize_sheets_service()
        users_data = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
        
        # Skip header row
        users_data = users_data[1:] if len(users_data) > 1 else []
        
        return render_template('users.html', users=users_data)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return render_template('users.html', users=[])

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@role_required(['Owner'])
def add_user():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            
            # Initialize services
            sheets_service = initialize_sheets_service()
            
            # Check if username already exists
            users = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
            for user in users:
                if len(user) > 1 and user[1] == username:
                    flash('Username already exists', 'error')
                    return render_template('add_user.html')
            
            # Add user to Google Sheets
            hashed_password = generate_password_hash(password)
            user_data = [[name, username, hashed_password, role]]
            append_sheet_data(sheets_service, SPREADSHEET_ID, "Users", user_data)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Add User", f"Added user: {username}")
            
            flash('User added successfully', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            flash(f'Error adding user: {str(e)}', 'error')
    
    return render_template('add_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Owner'])
def edit_user(user_id):
    try:
        sheets_service = initialize_sheets_service()
        users = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
        
        # Skip header row and adjust index
        if user_id >= len(users) - 1 or user_id < 0:
            flash('User not found', 'error')
            return redirect(url_for('users'))
        
        user = users[user_id + 1]  # +1 to account for header row
        
        if request.method == 'POST':
            name = request.form.get('name')
            username = request.form.get('username')
            role = request.form.get('role')
            password = request.form.get('password')
            
            # Check if username already exists (if changed)
            if username != user[1]:
                for u in users:
                    if len(u) > 1 and u[1] == username:
                        flash('Username already exists', 'error')
                        return render_template('edit_user.html', user=user, user_id=user_id)
            
            # Update user in Google Sheets
            hashed_password = user[2]
            if password:
                hashed_password = generate_password_hash(password)
            
            updated_user = [name, username, hashed_password, role]
            update_sheet_data(sheets_service, SPREADSHEET_ID, "Users", user_id + 2, updated_user)
            
            # Log activity
            log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Edit User", f"Updated user: {username}")
            
            flash('User updated successfully', 'success')
            return redirect(url_for('users'))
        
        return render_template('edit_user.html', user=user, user_id=user_id)
        
    except Exception as e:
        flash(f'Error editing user: {str(e)}', 'error')
        return redirect(url_for('users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Owner'])
def delete_user(user_id):
    try:
        sheets_service = initialize_sheets_service()
        users = get_sheet_data(sheets_service, SPREADSHEET_ID, "Users")
        
        # Skip header row and adjust index
        if user_id >= len(users) - 1 or user_id < 0:
            flash('User not found', 'error')
            return redirect(url_for('users'))
        
        user = users[user_id + 1]  # +1 to account for header row
        
        # Prevent deleting the last owner
        owner_count = 0
        for u in users:
            if len(u) > 3 and u[3] == "Owner":
                owner_count += 1
        
        if user[3] == "Owner" and owner_count <= 1:
            flash('Cannot delete the last owner user', 'error')
            return redirect(url_for('users'))
        
        # Delete user from Google Sheets
        delete_sheet_row(sheets_service, SPREADSHEET_ID, "Users", user_id + 2)
        
        # Log activity
        log_activity(sheets_service, SPREADSHEET_ID, current_user.username, "Delete User", f"Deleted user: {user[1]}")
        
        flash('User deleted successfully', 'success')
        
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('users'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                         title="Page Not Found", 
                         message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', 
                         title="Internal Server Error", 
                         message="Something went wrong on our end."), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', 
                         title="Access Denied", 
                         message="You don't have permission to access this page."), 403

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
