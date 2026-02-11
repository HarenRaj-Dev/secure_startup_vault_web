from flask import render_template, redirect, url_for, flash, current_app, send_file, request, send_from_directory
from flask_login import login_required, current_user
from vault import db
from vault.models import Company, Role, ActivityLog, File, User, memberships
from vault.companies import companies_bp
from vault.companies.forms import CompanyForm, RoleForm, AddUserForm
from vault.main.forms import UploadFileForm
from vault.crypto_utils import encrypt_file_data, decrypt_file_data
from vault.companies.services import log_activity, has_permission
from werkzeug.utils import secure_filename
from flask_wtf.csrf import generate_csrf
from sqlalchemy import select, insert, update, delete
import os
import uuid
import io

def get_user_companies():
    """Helper function to get all companies the current user has access to"""
    from sqlalchemy import select
    owned_companies = Company.query.filter_by(owner_id=current_user.id).all()
    member_companies_query = db.session.execute(
        select(Company).join(memberships, Company.id == memberships.c.company_id).where(memberships.c.user_id == current_user.id)
    ).all()
    member_companies = [row[0] for row in member_companies_query]
    return list(set(owned_companies + member_companies))

@companies_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_company():
    form = CompanyForm()
    if form.validate_on_submit():
        new_company = Company(
            name=form.name.data,
            password=form.password.data,
            owner_id=current_user.id
        )
        db.session.add(new_company)
        db.session.commit()
        
        # Create a default Admin role for the company
        admin_role = Role(
            name="Administrator", 
            company_id=new_company.id, 
            perm_admin=True,
            perm_view=True,
            perm_modify=True,
            perm_upload=True,
            perm_download=True,
            perm_logs=True,
            perm_remove_user=True,
            perm_manage_roles=True,
            perm_add_users=True
        )
        db.session.add(admin_role)
        db.session.commit()
        
        flash(f'Company {new_company.name} created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    # Pass a dictionary representing a new company to avoid the 'Undefined' error
    return render_template('companies/company_settings.html',form=form, company={'name': 'New Company'}, csrf_token=generate_csrf(), companies=get_user_companies())

@companies_bp.route('/<int:company_id>/settings', methods=['GET', 'POST'])
@login_required
def company_settings(company_id):
    company = Company.query.get_or_404(company_id)
    # Ensure only the owner can see settings
    if company.owner_id != current_user.id:
        flash("Only the owner can access settings.", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    
    form = CompanyForm()
    
    if request.method == 'GET':
        form.name.data = company.name
        form.password.data = company.password

    if form.validate_on_submit():
        # SECURITY CHECK: Verify user's password before allowing changes
        verify_pass = form.verify_password.data
        from werkzeug.security import check_password_hash
        if not check_password_hash(current_user.password, verify_pass):
            flash("Incorrect password. Changes not saved.", "danger")
            return redirect(url_for('companies.company_settings', company_id=company_id))

        company.name = form.name.data
        company.password = form.password.data
        
        if form.logo.data:
            logo_file = form.logo.data
            raw_name = secure_filename(logo_file.filename)
            logo_filename = f"{uuid.uuid4().hex}_{raw_name}"
            # Store in DB
            company.logo = os.path.join('logos', logo_filename) # Keep relative path for consistency if needed, or just filename
            company.logo_data = logo_file.read() # Store binary
            
        db.session.commit()
        from vault.companies.services import log_activity
        log_activity(company_id, current_user.email, "Updated company settings")
        flash("Company settings updated successfully!", "success")
        return redirect(url_for('companies.company_settings', company_id=company_id))
    
    return render_template('companies/company_settings.html', company=company, form=form, csrf_token=generate_csrf(), companies=get_user_companies())

@companies_bp.route('/<int:company_id>/delete', methods=['POST'])
@login_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    if company.owner_id != current_user.id:
        flash("Only the owner can delete the company.", "danger")
        return redirect(url_for('companies.company_settings', company_id=company_id))
    
    # SECURITY CHECK
    verify_pass = request.form.get('verify_password')
    from werkzeug.security import check_password_hash
    if not verify_pass or not check_password_hash(current_user.password, verify_pass):
        flash("Incorrect password. Company deletion aborted.", "danger")
        return redirect(url_for('companies.company_settings', company_id=company_id))

    # Delete associated memberships first
    from sqlalchemy import delete
    db.session.execute(delete(memberships).where(memberships.c.company_id == company_id))
    
    # Delete associated files, roles, logs, etc.
    File.query.filter_by(company_id=company_id).delete()
    Role.query.filter_by(company_id=company_id).delete()
    ActivityLog.query.filter_by(company_id=company_id).delete()
    db.session.delete(company)
    db.session.commit()
    flash("Company deleted successfully.", "success")
    return redirect(url_for('main.dashboard'))

@companies_bp.route('/<int:company_id>/remove_logo', methods=['POST'])
@login_required
def remove_logo(company_id):
    company = Company.query.get_or_404(company_id)
    if company.owner_id != current_user.id:
        flash("Only the owner can remove the logo.", "danger")
        return redirect(url_for('companies.company_settings', company_id=company_id))
    
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        flash("CSRF validation failed.", "danger")
        return redirect(url_for('companies.company_settings', company_id=company_id))

    # SECURITY CHECK
    verify_pass = request.form.get('verify_password')
    from werkzeug.security import check_password_hash
    if not verify_pass or not check_password_hash(current_user.password, verify_pass):
        flash("Incorrect password. Logo removal aborted.", "danger")
        return redirect(url_for('companies.company_settings', company_id=company_id))
    
    if company.logo and company.logo != 'logo.svg':
        # Just clear the DB fields
        company.logo = 'logo.svg'
        company.logo_data = None
        db.session.commit()
        log_activity(company_id, current_user.email, "Removed company logo")
        flash("Logo removed successfully.", "success")
    else:
        flash("No logo to remove.", "info")
    
    return redirect(url_for('companies.company_settings', company_id=company_id))

@companies_bp.route('/<int:company_id>/files')
@login_required
def company_files(company_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_view'):
        flash("Access Denied", "danger")
        return redirect(url_for('main.dashboard'))
    
    files = File.query.filter_by(company_id=company_id).all()
    
    # Calculate file sizes
    for file in files:
        if file.data:
            file.size = len(file.data)
        else:
            file.size = 0
    
    form = UploadFileForm()  # ← Added missing form initialization
    can_manage_roles = has_permission(current_user, company_id, 'perm_manage_roles')
    can_view_logs = has_permission(current_user, company_id, 'perm_logs')
    return render_template('companies/company_files.html', company=company, files=files, form=form, can_manage_roles=can_manage_roles, can_view_logs=can_view_logs, csrf_token=generate_csrf(), companies=get_user_companies())

@companies_bp.route('/<int:company_id>/upload', methods=['POST'])
@login_required
def upload_company_file(company_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_upload'):
        flash("Access Denied", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    
    form = UploadFileForm()
    if form.validate_on_submit():
        file_storage = form.file.data
        original_filename = file_storage.filename
        # Defensive: validate extension server-side
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower().lstrip('.')
        allowed = {'pdf', 'txt', 'docx', 'png', 'jpg', 'jpeg'}
        if ext not in allowed:
            flash('File type not allowed. Allowed: PDF, TXT, DOCX, PNG, JPG', 'danger')
            return redirect(url_for('companies.company_files', company_id=company_id))

        # Encrypt
        file_content = file_storage.read()
        encrypted_data, encrypted_aes_key, iv = encrypt_file_data(file_content, current_user.rsa_public_key)
        
        # Save to DB
        unique_name = str(uuid.uuid4())
        # file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
        
        # with open(file_path, 'wb') as f:
        #     f.write(encrypted_data)
        
        # DB
        new_file = File(
            filename=original_filename,
            encrypted_name=unique_name,
            data=encrypted_data, # Store file content
            user_id=current_user.id,
            company_id=company_id,
            encrypted_aes_key=encrypted_aes_key,
            iv=iv
        )
        db.session.add(new_file)
        db.session.commit()
        
        log_activity(company_id, current_user.email, f"Uploaded file: {original_filename}")
        flash(f'File {original_filename} uploaded to company!', 'success')
    else:
        # If form validation fails, show the error
        if form.file.errors:
            flash(str(form.file.errors[0]), 'danger')
    return redirect(url_for('companies.company_files', company_id=company_id))

@companies_bp.route('/<int:company_id>/download/<int:file_id>')
@login_required
def download_company_file(company_id, file_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_download'):
        flash("Access Denied", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    
    try:
        file_record = File.query.get_or_404(file_id)
        if file_record.company_id != company_id:
            flash("File not found in this company.", "danger")
            return redirect(url_for('companies.company_files', company_id=company_id))
        
        # Read encrypted data from DB
        encrypted_data = file_record.data
        if not encrypted_data:
             flash("File content not found.", "danger")
             return redirect(url_for('companies.company_files', company_id=company_id))
        
        # Decrypt
        decrypted_data = decrypt_file_data(
            encrypted_data, 
            file_record.encrypted_aes_key, 
            file_record.iv, 
            current_user.rsa_private_key
        )
        
        log_activity(company_id, current_user.email, f"Downloaded file: {file_record.filename}")
        
        # Create a BytesIO object fresh for this request
        file_stream = io.BytesIO(decrypted_data)
        
        return send_file(
            file_stream,
            download_name=file_record.filename,
            as_attachment=True,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))

@companies_bp.route('/<int:company_id>/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_company_file(company_id, file_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_modify'):
        flash("Access Denied", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    
    file_to_delete = File.query.get_or_404(file_id)
    if file_to_delete.company_id != company_id:
        flash("File not found in this company.", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    
    db.session.delete(file_to_delete)
    db.session.commit()
    log_activity(company_id, current_user.email, f"Deleted file: {file_to_delete.filename}")
    flash("File removed from company vault.", "success")
    return redirect(url_for('companies.company_files', company_id=company_id))

@companies_bp.route('/<int:company_id>/roles', methods=['GET', 'POST'])
@login_required
def company_roles(company_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_manage_roles'):
        flash("You don't have permission to manage roles.", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    roles = Role.query.filter_by(company_id=company_id).all()
    return render_template('companies/company_roles.html', company=company, roles=roles, companies=get_user_companies())

@companies_bp.route('/<int:company_id>/roles/config', methods=['GET', 'POST'])
@login_required
def role_config(company_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_manage_roles'):
        flash("You don't have permission to manage roles.", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    form = RoleForm()
    if form.validate_on_submit():
        new_role = Role(
            name=form.name.data,
            company_id=company_id,
            perm_admin=form.perm_admin.data,
            perm_view=form.perm_view.data,
            perm_modify=form.perm_modify.data,
            perm_upload=form.perm_upload.data,
            perm_download=form.perm_download.data,
            perm_logs=form.perm_logs.data,
            perm_remove_user=form.perm_remove_user.data,
            perm_manage_roles=form.perm_manage_roles.data,
            perm_add_users=form.perm_add_users.data
        )
        db.session.add(new_role)
        db.session.commit()
        flash("Role created!", "success")
        return redirect(url_for('companies.company_roles', company_id=company_id))
    return render_template('companies/role_config.html', company=company, form=form, submit_text="Create Role", companies=get_user_companies())

@companies_bp.route('/<int:company_id>/roles/config/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role_config(company_id, role_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_manage_roles'):
        flash("You don't have permission to manage roles.", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    role = Role.query.get_or_404(role_id)
    if role.company_id != company_id:
        flash("Role not found.", "danger")
        return redirect(url_for('companies.company_roles', company_id=company_id))
    
    form = RoleForm()
    if form.validate_on_submit():
        role.name = form.name.data
        role.perm_admin = form.perm_admin.data
        role.perm_view = form.perm_view.data
        role.perm_modify = form.perm_modify.data
        role.perm_upload = form.perm_upload.data
        role.perm_download = form.perm_download.data
        role.perm_logs = form.perm_logs.data
        role.perm_remove_user = form.perm_remove_user.data
        role.perm_manage_roles = form.perm_manage_roles.data
        role.perm_add_users = form.perm_add_users.data
        db.session.commit()
        flash("Role updated!", "success")
        return redirect(url_for('companies.company_roles', company_id=company_id))
    
    # Pre-fill form
    form.name.data = role.name
    form.perm_admin.data = role.perm_admin
    form.perm_view.data = role.perm_view
    form.perm_modify.data = role.perm_modify
    form.perm_upload.data = role.perm_upload
    form.perm_download.data = role.perm_download
    form.perm_logs.data = role.perm_logs
    form.perm_remove_user.data = role.perm_remove_user
    form.perm_manage_roles.data = role.perm_manage_roles
    form.perm_add_users.data = role.perm_add_users
    
    return render_template('companies/role_config.html', company=company, form=form, role=role, submit_text="Update Role", companies=get_user_companies())

@companies_bp.route('/<int:company_id>/roles/delete/<int:role_id>', methods=['POST'])
@login_required
def delete_role(company_id, role_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_manage_roles'):
        flash("You don't have permission to manage roles.", "danger")
        return redirect(url_for('companies.company_roles', company_id=company_id))
    
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        flash("CSRF validation failed.", "danger")
        return redirect(url_for('companies.company_roles', company_id=company_id))
    
    role = Role.query.get_or_404(role_id)
    if role.company_id != company_id:
        flash("Role not found.", "danger")
        return redirect(url_for('companies.company_roles', company_id=company_id))
    
    # Check if role is assigned to any users
    from sqlalchemy import select
    users_with_role = db.session.execute(select(memberships).where(memberships.c.role_id == role_id)).all()
    if users_with_role:
        flash("Cannot delete a role that is assigned to users. Please reassign them first.", "danger")
        return redirect(url_for('companies.company_roles', company_id=company_id))
    
    role_name = role.name
    db.session.delete(role)
    db.session.commit()
    log_activity(company_id, current_user.email, f"Deleted role: {role_name}")
    flash("Role deleted successfully.", "success")
    return redirect(url_for('companies.company_roles', company_id=company_id))

@companies_bp.route('/<int:company_id>/logs')
@login_required
def company_logs(company_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_logs'):
        flash("You don't have permission to view activity logs.", "danger")
        return redirect(url_for('companies.company_files', company_id=company_id))
    logs = ActivityLog.query.filter_by(company_id=company_id).order_by(ActivityLog.timestamp.desc()).all()
    return render_template('companies/company_logs.html', company=company, logs=logs, companies=get_user_companies())

@companies_bp.route('/<int:company_id>/users')
@login_required
def company_users(company_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_view'):
        flash("Access Denied", "danger")
        return redirect(url_for('main.dashboard'))
    
    # Fetch members
    members = []
    memberships_query = db.session.execute(select(memberships).where(memberships.c.company_id == company_id)).all()
    for membership in memberships_query:
        user = User.query.get(membership.user_id)
        role = Role.query.get(membership.role_id) if membership.role_id else None
        members.append({
            'user': user,
            'role': role,
            'is_owner': user.id == company.owner_id
        })
    
    can_remove_user = has_permission(current_user, company_id, 'perm_remove_user')
    can_add_users = has_permission(current_user, company_id, 'perm_add_users')
    can_manage_roles = has_permission(current_user, company_id, 'perm_manage_roles')
    can_view_logs = has_permission(current_user, company_id, 'perm_logs')
    
    return render_template('companies/company_users.html', company=company, members=members, can_remove_user=can_remove_user, can_add_users=can_add_users, can_manage_roles=can_manage_roles, can_view_logs=can_view_logs, csrf_token=generate_csrf(), companies=get_user_companies())

@companies_bp.route('/<int:company_id>/add_user', methods=['GET', 'POST'])
@login_required
def add_company_user(company_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_add_users'):
        flash("You don't have permission to add users.", "danger")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    form = AddUserForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('companies.add_company_user', company_id=company_id))
        
        # Check if already in company
        from sqlalchemy import select
        existing = db.session.execute(select(memberships).where(memberships.c.user_id == user.id, memberships.c.company_id == company_id)).first()
        if existing:
            flash("User already in company.", "danger")
            return redirect(url_for('companies.company_users', company_id=company_id))
        
        # Add to memberships with no role
        from sqlalchemy import insert
        db.session.execute(insert(memberships).values(user_id=user.id, company_id=company_id, role_id=None))
        db.session.commit()
        
        log_activity(company_id, current_user.email, f"Added user: {email}")
        flash("User added to company.", "success")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    return render_template('companies/add_user.html', company=company, form=form, companies=get_user_companies())

@companies_bp.route('/<int:company_id>/edit_user_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user_role(company_id, user_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_manage_roles'):
        flash("You don't have permission to manage roles.", "danger")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    user = User.query.get_or_404(user_id)
    
    # Check if user is in company
    from sqlalchemy import select
    membership = db.session.execute(select(memberships).where(memberships.c.user_id == user_id, memberships.c.company_id == company_id)).first()
    if not membership:
        flash("User not in company.", "danger")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    roles = Role.query.filter_by(company_id=company_id).all()
    
    if request.method == 'POST':
        role_id = request.form.get('role_id')
        if role_id == 'none':
            new_role_id = None
        else:
            new_role_id = int(role_id)
        
        # Update membership
        from sqlalchemy import update
        db.session.execute(update(memberships).where(memberships.c.user_id == user_id, memberships.c.company_id == company_id).values(role_id=new_role_id))
        db.session.commit()
        
        log_activity(company_id, current_user.email, f"Changed role for user: {user.email}")
        flash("User role updated.", "success")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    # Get current role
    current_role_id = membership[2]  # role_id is the third column
    current_role = Role.query.get(current_role_id) if current_role_id else None
    
    return render_template('companies/edit_user_role.html', company=company, user=user, roles=roles, current_role=current_role, csrf_token=generate_csrf(), companies=get_user_companies())

@companies_bp.route('/<int:company_id>/remove_user/<int:user_id>', methods=['POST'])
@login_required
def remove_user(company_id, user_id):
    company = Company.query.get_or_404(company_id)
    if not has_permission(current_user, company_id, 'perm_remove_user'):
        flash("You don't have permission to remove users.", "danger")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    user = User.query.get_or_404(user_id)
    if user.id == company.owner_id:
        flash("Cannot remove the company owner.", "danger")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    # Check if user is in company
    from sqlalchemy import select
    membership = db.session.execute(select(memberships).where(memberships.c.user_id == user_id, memberships.c.company_id == company_id)).first()
    if not membership:
        flash("User not in company.", "danger")
        return redirect(url_for('companies.company_users', company_id=company_id))
    
    # Remove from memberships
    db.session.execute(memberships.delete().where(memberships.c.user_id == user_id, memberships.c.company_id == company_id))
    db.session.commit()
    
    log_activity(company_id, current_user.email, f"Removed user: {user.email}")
    flash("User removed from company.", "success")
    return redirect(url_for('companies.company_users', company_id=company_id))


@companies_bp.route('/logo/<path:filename>')
def serve_logo(filename):
    """Serve uploaded logo files from the database."""
    # Try to find company with this logo
    company = Company.query.filter(Company.logo.like(f"%{filename}%")).first()
    
    if company and company.logo_data:
        return send_file(
            io.BytesIO(company.logo_data),
            mimetype='image/png', # Assuming PNG/JPG, browser handles it well usually
            as_attachment=False,
            download_name=filename
        )
            
    # Fallback to static default
    return redirect(url_for('static', filename='img/logo.svg'))