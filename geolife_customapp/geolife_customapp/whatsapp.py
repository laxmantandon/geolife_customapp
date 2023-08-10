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
        customers = frappe.db.sql("SELECT name, mobile_no, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no <> ''", as_dict=1)
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
                        "customer": cust.name,
                        "customer Name": cust.customer_name,
                        "as on Date" : frappe.utils.today(),
                        "Total Outstanding": outstanding[0].total_outstanding
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

                html = frappe.render_template('frappe/www/printview.html',
                    { "body": html, "css": get_print_style(), "title": "Customer Due 150 Days"}
                )

                send_whatsapp_report(html, "Customer Due 150 Days", cust.customer_primary_contact, "150days", outstanding)

                doc = frappe.get_doc("Customer", cust.name)
                doc.add_comment("Comment", text=f"WHATSAPP for Account Block Notification Sent On {cust.mobile_no}")
            
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
            "to": receiver,
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
        frappe.log_error(f"error = {str(e)}")

def send_cash_discount_whatsapp():

    send_whatsapp_for_cash_discount = frappe.db.get_single_value("Geolife Settings", "send_whatsapp_for_cash_discount")
    
    if send_whatsapp_for_cash_discount == 0:
        return
    
    try:
        customers = frappe.db.sql("SELECT name, mobile_no, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no <> '' and name = 'AMZ-CUST-0001'", as_dict=1)
        company = 'Geolife Agritech India Private Limited'
        
        for cust in customers:
            result = []
            total_cd_amount = 0
            bills = frappe.db.sql("""
                SELECT 
                    a.customer as party,
                    a.posting_date,a.effective_date, IF(a.effective_date != '', a.effective_date, a.posting_date) as EffectiveDate,
                    DATE_ADD(IF(a.effective_date != '', a.effective_date, a.posting_date), INTERVAL 120 DAY) due_date,
                    a.name as reference_no,
                    (a.grand_total + a.rounding_adjustment) as opening_amount,
                    (a.grand_total + a.rounding_adjustment) - a.outstanding_amount as receipt_amount,
                    a.outstanding_amount as closing_amount,
                    -- DATEDIFF(CURDATE(), DATE_ADD(IF(effective_date != '', effective_date, posting_date), INTERVAL 120 DAY)) due_days,
                    "" due_days,
                    a.status,
                    0 cd_percent,
                    0 cd_amount,
                    0 sales_return,
                    0 adjustments,
                    0 cheque_return,
                    0 payments,
                    "" due_days_for_cd,
                    "" cd_opportunity,
                    "Sales" type,
                    a.scheme_applicable
                FROM
                    `tabSales Invoice` a
                WHERE
                    a.customer = %s AND a.company = %s
                    AND a.docstatus = 1
                    AND a.is_return = 0
                    AND a.outstanding_amount > 0
                    -- AND a.scheme_applicable in ('Advance Booking Lifting Scheme April 2023', 'Ultramax Discount Scheme 23-24', 'Spider Scheme 23-24', 'Jodi No 1 Scheme 23-24',' Plus Kharif Booking Scheme 23-24', 'Pesticides Scheme 23-24', 'Cylinder Scheme 23-24', 'Georrhiza Scheme 23-24', 'Bactogang Seed Scheme 23-24', 'Annual Discount Scheme 23-24', 'Advance Booking Lifting Scheme May 2023', 'Mitti Ka Shringar 23-24',	'Mitti Ka Shringar 23-24 KRT', 'Vigore Lifting Scheme  23-24', 'Small Pack Gift Scheme 23-24', 'Advance Booking Lifting Scheme June 2023')
                ORDER BY a.posting_date
            """, (cust.name, company), as_dict=1)

            if bills:
                for bill in bills:

                    due_days = frappe.utils.date_diff(frappe.utils.today(), bill["EffectiveDate"]) or 0

                    if bill.get("scheme_applicable") in ['Advance Booking Lifting Scheme April 2023', 'Ultramax Discount Scheme 23-24', 'Spider Scheme 23-24', 'Jodi No 1 Scheme 23-24',' Plus Kharif Booking Scheme 23-24', 'Pesticides Scheme 23-24', 'Cylinder Scheme 23-24', 'Georrhiza Scheme 23-24', 'Bactogang Seed Scheme 23-24', 'Annual Discount Scheme 23-24', 'Advance Booking Lifting Scheme May 2023', 'Mitti Ka Shringar 23-24',	'Mitti Ka Shringar 23-24 KRT', 'Vigore Lifting Scheme  23-24', 'Small Pack Gift Scheme 23-24', 'Advance Booking Lifting Scheme June 2023']:

                        bill["due_days"] = due_days
                        
                        x = frappe.db.sql("""
                            SELECT percent,to_days from `tabETPL Product Group CD` where parent = 'All Items Group' AND 
                            %s BETWEEN applicable_from AND applicable_to AND %s BETWEEN from_days AND to_days
                        """, (bill["EffectiveDate"], due_days), as_dict=1)
                    
                        if x:
                            cd_per = x[0].percent or 0
                            to_days = x[0].to_days or 0
                            due_days = bill["due_days"] or ""
                            bill["cd_percent"] = f"{cd_per} %"
                            bill["due_days"] = f"{due_days} "
                            bill["cd_amount"] = round((bill["closing_amount"] * cd_per) / 100)
                            bill["cd_opportunity"] = (bill["closing_amount"] * 9) / 100
                            bill["cd_loss"] = bill["cd_opportunity"] - bill["cd_amount"]
                            bill["valid_upto"] = frappe.utils.add_to_date(bill["EffectiveDate"], days=to_days) 
                    
                        else:
                            bill["cd_percent"] = f" 0 %"
                            due_days = bill["due_days"] or ""
                            bill["due_days"] = f"{due_days} "
                            bill["valid_upto"] = "NA"
                    else:
                        #due_days = bill["due_days"] or ""
                        bill["cd_percent"] = f"0 %"
                        bill["due_days"] = f"{due_days} "
                        bill["valid_upto"] = "NA"
                    result.append(bill)

                # add total row
                total_cd_amount = 0
                for t in result:
                    if t.get("type") == "Sales":
                        total_cd_amount = total_cd_amount + t.get("cd_amount") or 0
            
            if total_cd_amount > 0:

                filters = frappe._dict(
                    {
                        "company": company,
                        "customer": cust.name,
                        "customer Name": cust.customer_name,
                        "Report Date" : frappe.utils.today(),
                        "": "<b>Bill wise summary showing the cash discount on your outstanding invoices.</b>"
                    }
                )
                report_data = frappe.desk.query_report.run(
                    "Geolife Cash Discount - Distributor",
                    filters=filters
                )

                letter_head = frappe.get_doc('Letter Head', 'geolife')

                html = frappe.render_template('templates/CashDiscountDistributor.html',
                    {
                        "filters": filters,
                        "data": report_data["result"],
                        "title": "Cash Discount",
                        "columns": report_data["columns"],
                        "letter_head": letter_head
                    }
                )

                html = frappe.render_template('frappe/www/printview.html',
                    { "body": html, "css": get_print_style(), "title": "Cash Discount"}
                )

                send_cash_discount_whatsapp_report(html, "Cash Discount", cust.customer_primary_contact, "cash_discount")

                doc = frappe.get_doc("Customer", cust.name)
                doc.add_comment("Comment", text=f"WHATSAPP for Cash Discount Sent On {cust.mobile_no}")
            
    except Exception as e:
        frappe.log_error(e, "whatsapp_for_cash_discount_log")

def send_cash_discount_whatsapp_report(html, document_caption, contact, wa_template):
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
            "to": receiver,
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
        frappe.log_error(f"error = {str(e)}")

def send_ledger_whatsapp():

    send_whatsapp_for_ledger = frappe.db.get_single_value("Geolife Settings", "send_whatsapp_for_ledger")
    
    if send_whatsapp_for_ledger == 0:
        return
    
    try:
        customers = frappe.db.sql("SELECT name, customer_name, mobile_no, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no <> '' and name in ('AMZ-CUST-0001', 'MP-CUST-0815')", as_dict=1)
        company = 'Geolife Agritech India Private Limited'
        
        for cust in customers:
            if cust.get("mobile_no"):
                filters = frappe._dict(
                    {
                        "company": company,
                        "from_date": "2023-04-01",
                        "to_date": frappe.utils.today(),
                        "account":[],
                        "party_type": "Customer",
                        "party": [cust.name],
                        "party_name": cust.customer_name,
                        "group_by": "Group by Voucher (Consolidated)",
                        "cost_center":[],
                        "branch":[],
                        "project":[],
                        "include_dimensions":1,
                        "geo_show_taxes": 0,
                        "geo_show_inventory": 0,
                        "geo_show_remarks": 1,
                        "presentation_currency": ""
                    }
                )
                report_data = frappe.desk.query_report.run(
                    "General Ledger",
                    filters=filters
                )
                report_data["result"].pop()

                letter_head = frappe.get_doc('Letter Head', 'geolife')

                html = frappe.render_template('templates/GeneralLedger.html',
                    {
                        "filters": filters,
                        "data": report_data["result"],
                        "title": "Statement of Accounts",
                        "columns": report_data["columns"],
                        "letter_head": letter_head,
                        "terms_and_conditions": False,
                        "ageing": False,
                    }
                )

                html = frappe.render_template('frappe/www/printview.html',
                    { "body": html, "css": get_print_style(), "title": "Statement of Accounts"}
                )

                send_ledger_whatsapp_report(html, "Statement of Accounts", cust.customer_primary_contact, "ledger_statement_by_date", filters.get("from_date"), filters.get("to_date"))

                doc = frappe.get_doc("Customer", cust.name)
                doc.add_comment("Comment", text=f"WHATSAPP for Ledger Sent On {cust.mobile_no}")
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "whatsapp_for_ledger_log")

def send_ledger_whatsapp_report(html, document_caption, contact, wa_template, from_date, to_date):
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
            "to": receiver,
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
                                "text": frappe.format(from_date, {'fieldtype': 'Date'})
                            },
                            {
                                "type": "text",
                                "text": frappe.format(to_date, {'fieldtype': 'Date'})
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
        frappe.log_error(f"error = {str(e)}")
