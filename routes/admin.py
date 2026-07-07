from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import employees_collection
from forms import CSRFOnlyForm
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from utils import normalize_family
import re

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))

    form = CSRFOnlyForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            search_term = request.form.get('search', '').strip()
            return redirect(url_for('admin.admin_dashboard', search=search_term))
        else:
            flash('Invalid or missing CSRF token.', 'danger')
            return redirect(url_for('admin.admin_dashboard'))

    search = request.args.get('search', '').strip()
    query = {'role': {'$ne': 'admin'}}
    if search:
        exact_fields = ['employee_id', 'phone', 'gender', 'department', 'email']
        partial_fields = ['name']
        conditions = []
        # Exact match (case-insensitive)
        for field in exact_fields:
            conditions.append({
                field: {'$regex': f'^{re.escape(search)}$', '$options': 'i'}
            })

        # Partial match (case-insensitive)
        for field in partial_fields:
            conditions.append({
                field: {'$regex': f'{re.escape(search)}', '$options': 'i'}
            })

        if search.lower() == 'incomplete':
            conditions.append({'details_completed': {'$ne': True}})

        query['$or'] = conditions

    employees = list(employees_collection.find(query))
    return render_template('admin_dashboard.html', employees=employees, form=form)

@admin_bp.route('/employee/delete/<employee_id>', methods=['POST'])
def delete_employee(employee_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if employee_id == 'admin':
        flash('Cannot delete the admin account.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    from bson.errors import InvalidId
    
    emp_to_delete = None
    try:
        emp_to_delete = employees_collection.find_one({'_id': ObjectId(employee_id), 'role': {'$ne': 'admin'}})
    except InvalidId:
        pass
        
    if not emp_to_delete:
        emp_to_delete = employees_collection.find_one({'employee_id': employee_id, 'role': {'$ne': 'admin'}})

    if not emp_to_delete:
        flash("Employee not found or cannot be deleted.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    result = employees_collection.delete_one({'_id': emp_to_delete['_id']})

    if result.deleted_count:
        emp_name = emp_to_delete.get('name', 'Unknown')
        emp_code = emp_to_delete.get('employee_id', 'None')
        flash(f"Employee ID {emp_code}, name {emp_name}, has been deleted.", "success")
    else:
        flash("Employee not found or cannot be deleted.", "danger")

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete_selected', methods=['POST'])
def delete_selected():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))

    selected_ids = request.form.getlist('selected_ids[]')
    if not selected_ids:
        flash("No employees selected.", "warning")
        return redirect(url_for('admin.admin_dashboard'))

    from bson.objectid import ObjectId
    filtered_ids = []
    for eid in selected_ids:
        if eid and eid != 'admin':
            try:
                filtered_ids.append(ObjectId(eid))
            except:
                pass

    if not filtered_ids:
        flash("No valid employees selected.", "warning")
        return redirect(url_for('admin.admin_dashboard'))

    result = employees_collection.delete_many({
        '_id': {'$in': filtered_ids},
        'role': {'$ne': 'admin'}
    })
    flash(f"{result.deleted_count} employee(s) deleted.", "success")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/change_password', methods=['GET', 'POST'])
def admin_change_password():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "danger")
            return redirect(url_for('admin.admin_change_password'))

        admin = employees_collection.find_one({'role': 'admin'})
        if not admin or not check_password_hash(admin['password'], current_password):
            flash("Current password is incorrect.", "danger")
        else:
            employees_collection.update_one({'_id': admin['_id']}, {'$set': {'password': generate_password_hash(new_password)}})
            flash("Password updated successfully.", "success")
            return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin_change_password.html', is_admin=True)

@admin_bp.route('/admin/change_employee_password/<employee_id>', methods=['GET', 'POST'])
def change_employee_password(employee_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))

    employee = employees_collection.find_one({'employee_id': employee_id})
    if not employee:
        flash("Employee not found.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "danger")
            return redirect(url_for('admin.change_employee_password', employee_id=employee_id))

        employees_collection.update_one(
            {'employee_id': employee_id},
            {'$set': {'password': generate_password_hash(new_password)}}
        )
        flash(f"Password for {employee.get('name', 'Employee')} updated successfully.", "success")
        return redirect(url_for('main.employee_detail', employee_id=employee_id))

    return render_template('admin_change_password.html', employee_id=employee_id, is_admin=False)
