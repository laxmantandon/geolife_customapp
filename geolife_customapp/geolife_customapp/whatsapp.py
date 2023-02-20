import frappe
import json
import os
import time
from frappe.integrations.utils import make_get_request, make_post_request
import frappe.desk.query_report
from frappe.www.printview import get_print_style

from erevive_whatsapp.api.whatsapp import get_pdf_data, create_folder
from frappe.utils.file_manager import save_file
from frappe.utils import random_string


def send_account_block_whatsapp():

    send_whatsapp_for_account_block = frappe.db.get_single_value("Geolife Settings", "send_whatsapp_for_account_block")
    
    if send_whatsapp_for_account_block == 0:
        return
    
    try:
        # customers = frappe.db.sql("SELECT name, mobile_no from tabCustomer where mobile_no is not null", as_dict=1)
        customers = frappe.db.sql("SELECT name, mobile_no, customer_primary_contact from tabCustomer where name = 'AMZ-CUST-0001'", as_dict=1)
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

                filters = frappe._dict(
                    {
                        "company": company,
                        "customer": cust.name
                    }
                )
                report_data = frappe.desk.query_report.run(
                    "Customer Due 150 Days",
                    filters=filters
                )

                letter_head = frappe.get_doc('Letter Head', 'geolife')

                html = frappe.render_template('templates/CustomerDue150Days.html',
                    {
                        "filters": filters,
                        "data": report_data["result"],
                        "title": "Customer Due 150 Days",
                        "columns": report_data["columns"],
                        "letter_head": letter_head
                    }
                )

                # frappe.log_error(html, 'test')
                # html = frappe.render_template('frappe/public/js/frappe/views/reports/print_grid.html',
                #     {
                #         "filters": filters,
                #         "data": report_data["result"],
                #         "title": "Customer Due 150 Days",
                #         "columns": report_data["columns"]
                #     }
                # )

                html = frappe.render_template('frappe/www/printview.html',
                    { "body": html, "css": get_print_style(), "title": "Customer Due 150 Days"}
                )

                # frappe.log_error(report_data["result"], 'Data')
                # frappe.log_error(report_data["columns"], 'Columns')
                send_whatsapp_report(html, "Customer Due 150 Days", cust.customer_primary_contact, "150days", outstanding)

                # sms = f"Dear Sir, This is to inform you that your account is locked due to non payment of overdue outstanding Rs {outstanding[0].overdue} by more than 150Days as on {frappe.utils.today()}. Total Outstanding Amount Rs. {outstanding[0].total_outstanding}. We Request you to make payment of overdue amount immediately to unlock your account and for getting further sales and discount benefit on other invoices issued after this. Geolife Agritech India Pvt Ltd"
                # mobile_no = cust.mobile_no
                # template_id = "1507167454191431053"
            
                # url = f"http://sms.par-ken.com/api/smsapi?key=14a18a8729a432b3a332cdc9686a83f1&route=1&sender=GEOTFP&number={mobile_no}&sms={sms}&templateid={template_id}"
                # url = frappe.utils.get_url(url)
                
                # req = make_get_request(url)
                
                # doc = frappe.get_doc("Customer", cust.name)
                # doc.add_comment("Comment", text=f"{sms} - Sent On {mobile_no}")
            
    except Exception as e:
        frappe.log_error(e, "whatsapp_for_account_block_log")

def send_whatsapp_report(html, document_caption, contact, wa_template, outstanding):
    try:
        url = frappe.db.get_single_value("ETPL Whatsapp Settings", "url")
        version = frappe.db.get_single_value("ETPL Whatsapp Settings", "version")
        phone_number_id = frappe.db.get_single_value("ETPL Whatsapp Settings", "phone_number_id")
        token = frappe.db.get_single_value("ETPL Whatsapp Settings", "token")
        token = f"Bearer {token}"
        base_url = f"{url}/{version}/{phone_number_id}/messages"

        pdf_data = get_pdf_data(None, None, None, None, is_report=True, report_html=html)
        unique_hash = frappe.generate_hash()[:10]
        s_file_name = f"{unique_hash}.pdf"
        folder_name = create_folder("Whatsapp", "Home")
        saved_file = save_file(s_file_name, pdf_data, '', '', folder=folder_name, is_private=0)
        s_document_link = f"{frappe.utils.get_url()}/files/{saved_file.file_name}"
        receiver = frappe.db.get_value("Contact", contact, "mobile_no")
        if not receiver:
            frappe.throw("Mobile Number Not Specified")

        file_path = frappe.utils.get_files_path(saved_file.file_name)

        while not os.path.exists(file_path):
            time.sleep(1)

        payload = json.dumps({
            "messaging_product": "whatsapp",
            "to": "9926100041", #receiver,
            "type": "template",
            "template": {
                "name": wa_template,
                "language": {
                    "code": "en_US"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "link": s_document_link,
                                    "filename": document_caption
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": str(outstanding[0].overdue)
                            },
                            {
                                "type": "text",
                                "text": "150 Days"
                            },
                            {
                                "type": "text",
                                "text": frappe.utils.today()
                            },
                            {
                                "type": "text",
                                "text": str(outstanding[0].total_outstanding)
                            }
                        ]
                    }
                ]
            }
        })
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }

        response = make_post_request(
            base_url, headers=headers, data=payload)
        frappe.log_error(f"req = {str(payload)} Resp = {str(response)}")
        frappe.msgprint("Whatsapp Sent")

    except Exception as e:
        frappe.log_error(f"error = {str(e)} req = {str(payload)}")