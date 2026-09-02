# Copyright (c) 2026, Increatech Business Solution Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, today

class ZohoJobOpenings(Document):
	@property
	def get_target_date(self):
		if self.target_date:
			return self.target_date
		else:
			default_target_date_range = frappe.db.get_single_value("Zoho Recruit Settings", "default_target_date_range")
			return add_days(today(), int(default_target_date_range or 30))
 
