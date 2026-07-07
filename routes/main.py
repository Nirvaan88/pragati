from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bson import ObjectId
from models import employees_collection
from datetime import date
from utils import calc_age, normalize_family, _get_employee_by_session_id

main_bp = Blueprint('main', __name__)

def _get_numeric_age(dob_str):
    try:
        dob = date.fromisoformat(dob_str)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 0

@main_bp.route('/check_employee_id', methods=['GET'])
def check_employee_id():
    emp_id = request.args.get('employee_id', '').strip()
    mongo_id = request.args.get('mongo_id', '').strip()
    if not emp_id:
        return {'exists': False}
    query = {'employee_id': emp_id}
    if mongo_id and mongo_id != 'None':
        try:
            query['_id'] = {'$ne': ObjectId(mongo_id)}
        except Exception:
            pass
    exists = employees_collection.find_one(query) is not None
    return {'exists': exists}

@main_bp.route('/complete_profile', methods=['GET', 'POST'])
@main_bp.route('/complete_profile/<employee_id>', methods=['GET', 'POST'])
def complete_profile(employee_id=None):
    is_admin = session.get('role') == 'admin'
    is_user = session.get('role') == 'user'

    if is_admin and employee_id:
        employee = employees_collection.find_one({'_id': ObjectId(employee_id)})
        if not employee:
            flash("Employee not found.", "danger")
            return redirect(url_for('admin.admin_dashboard'))
    elif is_user and not employee_id:
        emp_id = session.get('mongo_id')
        employee = employees_collection.find_one({'_id': ObjectId(emp_id)})
        if not employee:
            flash("Employee not found.", "danger")
            return redirect(url_for('auth.dashboard'))
    else:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('auth.dashboard'))

    is_submitted = employee.get('details_completed', False)
    readonly = not is_admin and is_submitted
    show_submit = (not is_submitted) or is_admin
    show_logout = is_user and is_submitted
    show_admin_actions = is_admin and is_submitted

    if request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['family_members'] = []

        emp_id_form = form_data.get('employee_id', '').strip()
        if not emp_id_form:
            flash("Employee ID is required.", "danger")
            return redirect(request.url)
        conflict = employees_collection.find_one({'employee_id': emp_id_form, '_id': {'$ne': employee['_id']}})
        if conflict:
            flash("Employee ID already exists.", "danger")
            return redirect(request.url)
        form_data['employee_id'] = emp_id_form

        emp_dob = form_data.get('dob', '').strip()
        if not emp_dob or _get_numeric_age(emp_dob) < 18:
            flash("Employee must be at least 18 years old.", "danger")
            return redirect(request.url)

        emp_doj = form_data.get('date_of_joining', '').strip()
        if emp_dob and emp_doj:
            try:
                dob_d = date.fromisoformat(emp_dob)
                doj_d = date.fromisoformat(emp_doj)
                if doj_d <= dob_d:
                    flash("Date of Joining must be after Date of Birth.", "danger")
                    return redirect(request.url)
            except Exception:
                pass

        phone = form_data.get('phone', '').strip()
        if not phone.isdigit() or len(phone) != 10:
            flash("Phone number must be exactly 10 digits.", "danger")
            return redirect(request.url)

       
        import re
        email = form_data.get('email', '').strip() 
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash("Invalid email format.", "danger")
            return redirect(request.url)

        family_phones = set()
        family_names = set()

        marital_status = form_data.get('marital_status')
        if marital_status == 'married':
            spouse_name = form_data.pop('spouse_name', '').strip()
            spouse_dob = form_data.pop('spouse_dob', '')
            spouse_gender = form_data.pop('spouse_gender', '')
            spouse_age = calc_age(spouse_dob) if spouse_dob else ''
            if not spouse_name or not spouse_dob or not spouse_gender:
                flash("All spouse details are required for married employees.", "danger")
                return redirect(request.url)
            if _get_numeric_age(spouse_dob) < 18:
                flash("Spouse must be at least 18 years old.", "danger")
                return redirect(request.url)
            family_names.add(spouse_name.lower())
            form_data['family_members'].append({
                'relationship': 'Spouse',
                'name': spouse_name,
                'date_of_birth': spouse_dob,               
                'gender': spouse_gender,
                'age': spouse_age
            })
        else:
            for key in ['spouse_name', 'spouse_dob', 'spouse_gender', 'spouse_age']:
                form_data.pop(key, None)

        try:
            total_children = int(request.form.get('total_children', 0))
        except ValueError:
            total_children = 0

        if marital_status in ['married', 'divorced/widowed']:
            for i in range(total_children):
                name = request.form.get(f'child_name_{i}', '').strip()
                dob = request.form.get(f'child_dob_{i}', '')
                phone_c = request.form.get(f'child_phone_{i}', '').strip()
                gender = request.form.get(f'child_gender_{i}', '')
                age = calc_age(dob) if dob else ''
                if not name or not dob or not gender:
                    flash(f"All fields for child {i+1} are required.", "danger")
                    return redirect(request.url)
                lname = name.lower()
                if lname in family_names:
                    flash(f"Duplicate family member name '{name}' is not allowed.", "danger")
                    return redirect(request.url)
                if phone_c and phone_c in family_phones:
                    flash(f"Duplicate phone '{phone_c}' among family members.", "danger")
                    return redirect(request.url)
                family_names.add(lname)
                if phone_c:
                    family_phones.add(phone_c)
                form_data['family_members'].append({
                    'relationship': 'Child',
                    'name': name,
                    'date_of_birth': dob,
                    'phone': phone_c,
                    'gender': gender,
                    'age': age
                })

        try:
            total_parents = int(request.form.get('total_parents', 0))
        except ValueError:
            total_parents = 0
        seen_parent_rels = set()
        for i in range(total_parents):
            rel = request.form.get(f'parent_relationship_{i}', '')
            name = request.form.get(f'parent_name_{i}', '').strip()
            dob = request.form.get(f'parent_dob_{i}', '')
            age = request.form.get(f'parent_age_{i}', '') or (calc_age(dob) if dob else '')
            if rel in seen_parent_rels:
                flash(f"Duplicate parent relationship '{rel}' is not allowed.", "danger")
                return redirect(request.url)
            if name.lower() in family_names:
                flash(f"Duplicate parent name '{name}' is not allowed.", "danger")
                return redirect(request.url)
            seen_parent_rels.add(rel)
            family_names.add(name.lower())
            form_data['family_members'].append({
                'relationship': rel,
                'name': name,
                'date_of_birth': dob,
                'age': age
            })

        if is_user:
            form_data['details_completed'] = True
            session['mongo_id'] = str(employee['_id'])

        employees_collection.update_one({'_id': employee['_id']}, {'$set': form_data})

        if is_admin:
            flash("Changes saved successfully.", "success")
            return redirect(url_for('main.employee_detail', employee_id=form_data['employee_id']))
        
          #  session['details_completed'] = True  # Update session to indicate that profile is completed

        flash("Profile submitted. You cannot edit it further. Please contact admin for any changes.", "success")
        return redirect(url_for('main.employee_detail'))

    return render_template(
        "complete_profile.html",
        employee=normalize_family(employee),
        is_admin=is_admin,
        readonly=readonly,
        show_submit=show_submit,
        show_logout=show_logout,
        show_admin_actions=show_admin_actions,
        current_date=date.today().isoformat()
    )

@main_bp.route('/employee_detail')
@main_bp.route('/employee_detail/<employee_id>')
def employee_detail(employee_id=None):
    role = session.get('role')

    # Block unauthorized access
    if role not in ['user', 'admin']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))

    # Admin can view any profile by ID
    if role == 'admin' and employee_id:
        from bson.errors import InvalidId
        employee = None
        try:
            employee = employees_collection.find_one({'_id': ObjectId(employee_id)})
        except InvalidId:
            pass
            
        if not employee:
            employee = employees_collection.find_one({'employee_id': employee_id})
            
        if not employee:
            flash('Employee not found.', 'danger')
            return redirect(url_for('admin.admin_dashboard'))

    # Employee can view only their own profile
    else:
        emp_id = session.get('mongo_id')
        employee = _get_employee_by_session_id(emp_id)

        if not employee:
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.dashboard'))

        if not employee.get('details_completed', False):
            flash("Please complete your profile first.", "warning")
            return redirect(url_for('main.complete_profile'))

    return render_template("employee_detail.html", employee=normalize_family(employee))

@main_bp.route('/api/save_draft', methods=['POST'])
def save_draft():
    if session.get('role') != 'user':
        return {'success': False, 'message': 'Unauthorized'}, 403
        
    emp_id = session.get('mongo_id')
    employee = employees_collection.find_one({'_id': ObjectId(emp_id)})
    if not employee:
        return {'success': False, 'message': 'Not found'}, 404
        
    if employee.get('details_completed', False):
        return {'success': False, 'message': 'Already completed'}, 400

    form_data = request.form.to_dict()
    form_data['family_members'] = []
    
    marital_status = form_data.get('marital_status')
    if marital_status == 'married':
        spouse_name = form_data.pop('spouse_name', '').strip()
        spouse_dob = form_data.pop('spouse_dob', '')
        spouse_gender = form_data.pop('spouse_gender', '')
        spouse_age = calc_age(spouse_dob) if spouse_dob else ''
        if spouse_name or spouse_dob or spouse_gender:
            form_data['family_members'].append({
                'relationship': 'Spouse',
                'name': spouse_name,
                'date_of_birth': spouse_dob,               
                'gender': spouse_gender,
                'age': spouse_age
            })
    else:
        for key in ['spouse_name', 'spouse_dob', 'spouse_gender', 'spouse_age']:
            form_data.pop(key, None)

    try:
        total_children = int(request.form.get('total_children', 0))
    except ValueError:
        total_children = 0

    if marital_status in ['married', 'divorced/widowed']:
        for i in range(total_children):
            name = request.form.get(f'child_name_{i}', '').strip()
            dob = request.form.get(f'child_dob_{i}', '')
            phone_c = request.form.get(f'child_phone_{i}', '').strip()
            gender = request.form.get(f'child_gender_{i}', '')
            age = calc_age(dob) if dob else ''
            
            if name or dob or gender:
                form_data['family_members'].append({
                    'relationship': 'Child',
                    'name': name,
                    'date_of_birth': dob,
                    'phone': phone_c,
                    'gender': gender,
                    'age': age
                })

    try:
        total_parents = int(request.form.get('total_parents', 0))
    except ValueError:
        total_parents = 0
        
    for i in range(total_parents):
        rel = request.form.get(f'parent_relationship_{i}', '')
        name = request.form.get(f'parent_name_{i}', '').strip()
        dob = request.form.get(f'parent_dob_{i}', '')
        age = request.form.get(f'parent_age_{i}', '') or (calc_age(dob) if dob else '')
        
        if rel or name:
            form_data['family_members'].append({
                'relationship': rel,
                'name': name,
                'date_of_birth': dob,
                'age': age
            })

    form_data.pop('details_completed', None)
    form_data.pop('csrf_token', None)

    employees_collection.update_one({'_id': employee['_id']}, {'$set': form_data})
    return {'success': True}
