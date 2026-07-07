# utils.py
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from bson.objectid import ObjectId
from bson import ObjectId, errors as bson_errors
from models import employees_collection

def calc_age(dob_str):
    try:
        dob = date.fromisoformat(dob_str)
        today = date.today()

        delta = relativedelta(today, dob)

        if delta.years == 0:
            if delta.months == 0:
                if delta.days <= 1:
                    return "Newborn"
                return f"{delta.days} days"
            elif delta.days > 15:
                return f"{delta.months + 1} months"
            return f"{delta.months} months"
        elif delta.years == 1 and delta.months == 0 and delta.days == 0:
            return "1 year"
        else:
            return f"{delta.years} years"
    except Exception:
        return ""

def normalize_family(emp):
    family_members = []

    spouse_info = {'name': '', 'date_of_birth': '', 'phone': '', 'gender': '', 'age': ''}
    children_info = []
    parents_info = []

    original_family = emp.get('family_members', []) or []

    for member in original_family:
        rel = member.get('relationship', '').strip()
        name = member.get('name', '').strip()
        dob = member.get('date_of_birth', '').strip()
        gender = member.get('gender', '').strip()
        phone = member.get('phone', '').strip()
        age = member.get('age') or (calc_age(dob) if dob else '')

        if not rel or not name:
            continue  # Skip invalid/incomplete entries

        # Normalize structure
        if rel == 'Spouse':
            spouse_info = {
                'name': name,
                'date_of_birth': dob,
                'phone': phone,
                'gender': gender,
                'age': age
            }
        elif rel == 'Child':
            children_info.append({
                'name': name,
                'date_of_birth': dob,
                'phone': phone,
                'gender': gender,
                'age': age,
                'relationship': 'Child'
            })
        elif rel in ['Mother', 'Father']:
            parents_info.append({
                'name': name,
                'date_of_birth': dob,
                'age': age,
                'relationship': rel
            })

        # Always include valid member
        family_members.append({
            'name': name,
            'date_of_birth': dob,
            'age': age,
            'gender': gender,
            'relationship': rel,
            'phone': phone
        })

    emp['spouse'] = spouse_info
    emp['children'] = children_info
    emp['parents'] = parents_info

    # Only replace family_members if valid entries exist
    if family_members:
        emp['family_members'] = family_members

    return emp



def format_date_ddmmyyyy(date_str):
    if not date_str:
        return ''
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y', '%Y.%m.%d', '%d.%m.%Y'):
        try:
            d = datetime.strptime(date_str, fmt)
            return d.strftime('%d-%m-%Y')
        except Exception:
            continue
    return date_str  # fallback

def _get_employee_by_session_id(emp_id):
    """
    Fetches employee by _id or employee_id string.
    Returns None if nothing found or invalid ID format.
    """
    if not emp_id:
        return None

    try:
        return employees_collection.find_one({'_id': ObjectId(emp_id)})
    except (bson_errors.InvalidId, TypeError):
        return employees_collection.find_one({'employee_id': emp_id})
