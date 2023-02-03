import frappe
from frappe.integrations.utils import make_get_request

def send_account_block_sms():
    
    try:
        customers = frappe.db.sql("SELECT name, mobile_no from tabCustomer where mobile_no is not null", as_dict=1)
        company = 'Geolife Agritech India Private Limited'
        
        for cust in customers:
            outstanding = frappe.db.sql("""
                SELECT 
                    customer as party,
                    posting_date,
                    name as voucher_no,
                    SUM(outstanding_amount) as closing,
                    SUM(outstanding_amount) as overdue,
                    DATEDIFF(CURDATE(), DATE_ADD(posting_date, INTERVAL 150 DAY)) due_days,
                    status,
                    (SELECT SUM(debit - credit) FROM `tabGL Entry` WHERE party = customer AND is_cancelled = 0 AND docstatus = 1) AS total_outstanding
                FROM
                    `tabSales Invoice`
                WHERE
                    customer = %s AND company = %s
                    AND status <> 'Paid'
                    AND is_return = 0
                    AND docstatus = 1
                    AND DATE_ADD(posting_date, INTERVAL 150 DAY) < CURDATE()
                HAVING total_outstanding > 0 AND overdue > 0
                """, (cust.name, company), as_dict=1)
            
            if outstanding:

                sms = f"Dear Sir, This is to inform you that your account is locked due to non payment of overdue outstanding Rs {outstanding[0].overdue} by more than 150Days as on {frappe.utils.today()}. Total Outstanding Amount Rs. {outstanding[0].total_outstanding}. We Request you to make payment of overdue amount immediately to unlock your account and for getting further sales and discount benefit on other invoices issued after this. Geolife Agritech India Pvt Ltd"
                mobile_no = cust.mobile_no
                template_id = "1507167454191431053"
            
                url = f"http://sms.par-ken.com/api/smsapi?key=14a18a8729a432b3a332cdc9686a83f1&route=1&sender=GEOTFP&number={mobile_no}&sms={sms}&templateid={template_id}"
                url = frappe.utils.get_url(url)
                
                req = make_get_request(url)
                
                doc = frappe.get_doc("Customer", cust.name)
                doc.add_comment("Comment", text=f"{sms} - Sent On {mobile_no}")
                
                # log = {"req": url, "res": req, "os": outstanding, "customer": customers}
                # frappe.log_error(log, "sms_for_account_block_log")
            
    except Exception as e:
        frappe.log_error(e, "sms_for_account_block_log")