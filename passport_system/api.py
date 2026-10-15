# Copyright (c) 2026, Hosa Mohammed and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_to_date, now


@frappe.whitelist(allow_guest=True)
def get_latest_passport():
    """جلب آخر طلب جواز تم إنشاؤه خلال آخر ساعة."""
    one_hour_ago = add_to_date(now(), hours=-1)

    name = frappe.db.get_value(
        "Passport Application",
        filters={"creation": [">=", one_hour_ago]},
        fieldname="name",
        order_by="creation desc",
    )

    if not name:
        return None

    try:
        doc = frappe.get_doc("Passport Application", name)
        return {
            "reference_number": doc.reference_number,
            "applicant_name": doc.applicant_name,
            "national_id": doc.national_id,
            "qr_data": doc.qr_data,
            "status": doc.status,
        }
    except frappe.DoesNotExistError:
        return None


@frappe.whitelist()
def get_passport_by_ref(reference_number: str | None = None):
    """جلب طلب جواز بواسطة الرقم المرجعي."""
    if not reference_number:
        return None

    reference_number = reference_number.strip()

    results = frappe.db.sql(
        """
        SELECT name
        FROM `tabPassport Application`
        WHERE reference_number = %s
        LIMIT 1
        """,
        (reference_number,),
        as_dict=True,
    )

    if not results:
        return None

    doc = frappe.get_doc("Passport Application", results[0].name)

    return {
        "name": doc.name,
        "reference_number": doc.reference_number,
        "applicant_name": doc.applicant_name,
        "national_id": doc.national_id,
        "date_of_birth": str(doc.date_of_birth) if doc.date_of_birth else "",
        "gender": doc.gender or "",
        "phone": doc.phone or "",
        "email": doc.email or "",
        "passport_type": doc.passport_type or "",
        "status": doc.status,
        "qr_data": doc.qr_data or "",
        "rejection_reason": doc.rejection_reason or "",
    }


@frappe.whitelist()
def process_workflow_action(doc_name: str | None = None, action: str | None = None):
    """تنفيذ انتقال Workflow على المستند."""
    if not doc_name or not action:
        frappe.throw("Missing parameters")

    doc = frappe.get_doc("Passport Application", doc_name)

    status_map = {
        "Verify": "Verified",
        "Approve": "Approved",
        "Reject": "Rejected",
        "Mark as Printed": "Printed",
    }

    new_status = status_map.get(action)
    if not new_status:
        frappe.throw(f"Invalid action: {action}")

    doc.status = new_status

    if action == "Mark as Printed":
        if doc.docstatus == 0:
            doc.submit()
    else:
        doc.save(ignore_permissions=True)

    return {
        "success": True,
        "new_status": doc.status,
    }