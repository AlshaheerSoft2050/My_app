from erpnext.selling.doctype.customer.customer import Customer
import frappe
from frappe import _
from frappe.utils import getdate, date_diff, add_days

class CustomCustomer(Customer):
    def before_save(self):
        now = getdate()
        
        # التحقق من عدد أرقام جواز السفر
        if len(self.custom_passport_number) != 6:
            frappe.throw(_("يجب أن يكون رقم الجواز مكونًا من 6 أرقام بالضبط."))
        
        # التحقق من تاريخ التأشيرة
        visa_date = getdate(self.custom_visa_date)
        if visa_date >= now:
            frappe.throw(_("يجب أن يكون تاريخ التأشيرة أصغر من تاريخ اليوم."))
        
        # التحقق من تاريخ الدخول
        entry_date = getdate(self.custom_entry_date)
        if entry_date > now:
            frappe.throw(_("يجب أن يكون تاريخ الدخول  اليوم أو تاريخًا سابقًا."))
        
        # تحويل عدد الأيام إلى عدد صحيح والتحقق منه
        days_stay = int(self.custom_number_of_days_of_stay)
        days_since_entry = date_diff(now, entry_date)
        
        # حساب الأيام المتبقية
        remaining_days = days_stay - days_since_entry
        remaining_days = max(remaining_days, 0)  # تأكيد أن القيمة غير سالبة
        
        # ضبط الأيام المتبقية لتكون غير قابلة للكتابة
        self.custom_remaining_days_of_stay = remaining_days
        
        # حساب تاريخ الخروج (التاريخ الموافق لآخر يوم من الأيام المتبقية للإقامة)
        self.custom_exit_date = add_days(entry_date, days_stay)

    

def update_remaining_days_for_all_customers():
    customers = frappe.db.get_list(
        "Customer",
        fields=["name", "custom_remaining_days_of_stay", "custom_entry_date", "custom_number_of_days_of_stay", "customer_name"]
    )
    now = getdate()
    for customer in customers:
        entry_date = getdate(customer.custom_entry_date)
        days_stay = int(customer["custom_number_of_days_of_stay"])
        days_since_entry = date_diff(now, customer["custom_entry_date"])
        # Calculate remaining days
        remaining_days = days_stay - days_since_entry
        remaining_days = max(remaining_days, 0)  # Ensure non-negative value
        frappe.db.set_value('Customer', customer["name"], 'custom_remaining_days_of_stay', remaining_days)
        if 0 < remaining_days <= 2:
            customer_name = customer["customer_name"]
            remaining_days = customer["custom_remaining_days_of_stay"]
            message = f"تنبيه: العميل {customer_name} لديه {remaining_days} يومًا فقط متبقية من إقامته."
            
            frappe.publish_realtime(
                event='msgprint',
                message=message,
                user=frappe.session.user
            )
    frappe.db.commit()       
