# Copyright (c) 2026, Hosa Mohammed and contributors
# For license information, please see license.txt

import io

import frappe
import qrcode
from frappe.model.document import Document
from frappe.utils import now_datetime, now
from frappe.utils.file_manager import save_file


class PassportApplication(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		applicant_name: DF.Data
		date_of_birth: DF.Date
		email: DF.Data | None
		gender: DF.Literal["Male", "Female"]
		national_id: DF.Data
		passport_type: DF.Literal["Urgent", "Normal"]
		phone: DF.Data | None
		qr_data: DF.AttachImage | None
		reference_number: DF.Data | None
		rejection_reason: DF.SmallText | None
		status: DF.Literal["Draft", "Pending", "Verified", "Approved", "Rejected", "Printed"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Passport Application"

	# ==================== Controller Methods ====================

	def after_insert(self):
		"""يُنفّذ بعد إنشاء المستند لأول مرة"""
		self.generate_reference_number()
		self.generate_qr_code()
		self.db_set("status", "Pending")

		# تخزين رقم الطلب في Cookie
		frappe.local.cookie_manager.set_cookie(
			"passport_last_ref",
			self.name,
			max_age=3600,
		)

	# ==================== Helper Methods ====================

	def generate_reference_number(self):
		"""توليد رقم مرجعي فريد: PA-YYYY-NNNNN"""
		if self.reference_number:
			return

		year = now_datetime().year
		count = frappe.db.count(
			"Passport Application",
			filters={"creation": [">=", f"{year}-01-01"]},
		) + 1

		ref = f"PA-{year}-{count:05d}"
		self.db_set("reference_number", ref)
		self.reference_number = ref

	def generate_qr_code(self):
		"""توليد QR Code وتخزينه كصورة مرفقة"""
		if self.qr_data:
			return

		# البيانات التي سيحتويها QR
		qr_text = (
			f"Passport Application\n"
			f"Reference: {self.reference_number}\n"
			f"Name: {self.applicant_name}\n"
			f"National ID: {self.national_id}\n"
			f"Date: {now()}"
		)

		# توليد صورة QR
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_H,
			box_size=10,
			border=4,
		)
		qr.add_data(qr_text)
		qr.make(fit=True)

		img = qr.make_image(fill_color="black", back_color="white")

		# تحويل الصورة إلى bytes
		buffer = io.BytesIO()
		img.save(buffer, format="PNG")
		buffer.seek(0)
		image_bytes = buffer.read()

		# حفظ الصورة كملف مرفق
		file_doc = save_file(
			fname=f"qr_{self.reference_number}.png",
			content=image_bytes,
			dt=self.doctype,
			dn=self.name,
			is_private=0,
			folder="Home/Attachments",
		)

		# حفظ رابط الملف في حقل QR Data
		self.db_set("qr_data", file_doc.file_url)
		self.qr_data = file_doc.file_url