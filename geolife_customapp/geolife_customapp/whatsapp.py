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
    frappe.enqueue(enqueue_send_account_block_whatsapp,queue="long")
    
def enqueue_send_account_block_whatsapp():
    try:
        customers = frappe.db.sql("SELECT name, mobile_no,customer_name, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no <> '' and branch not in ('Amazon', 'Karnataka Factory', 'Factory', 'Head Office','ECOM MH','ECOM KRT') and customer_active_type not in ('Closed')", as_dict=1)
        # customers = frappe.db.sql("SELECT name, mobile_no,customer_name, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no='9604035386' and branch not in ('Amazon', 'Karnataka Factory', 'Factory', 'Head Office') and customer_active_type not in ('Closed')", as_dict=1)
        company = 'Geolife Agritech India Private Limited'
        # frappe.log_error(customers,"customer list Try to Send 150")
        sended_whatsapp_customers_list = [d.customer for d in frappe.db.get_all("Geolife Whatsapp Log",filters={'posting_date':frappe.utils.nowdate(), 'template':'150days'}, fields=["customer"])]  
        for cust in customers:
            if cust.name not in sended_whatsapp_customers_list:
                if cust.mobile_no:
                    frappe.enqueue(cusutomer_enqueue_send_account_block_whatsapp,queue="long", cust=cust)

                    # frappe.log_error(cust,"Try to Send 150")
                    # outstanding = frappe.db.sql("""
                    #     SELECT 
                    #         customer as party,
                    #         posting_date,
                    #         name as voucher_no,
                    #         SUM(outstanding_amount) as closing,
                    #         SUM(outstanding_amount) as overdue,
                    #         DATEDIFF(CURDATE(), DATE_ADD(posting_date, INTERVAL 150 DAY)) due_days,
                    #         status,
                    #         (SELECT SUM(debit - credit) FROM `tabGL Entry` WHERE party = customer AND is_cancelled = 0 AND docstatus = 1) AS total_outstanding
                    #     FROM
                    #         `tabSales Invoice`
                    #     WHERE
                    #         customer = %s AND company = %s
                    #         AND status <> 'Paid'
                    #         AND is_return = 0
                    #         AND docstatus = 1
                    #         AND DATE_ADD(posting_date, INTERVAL 150 DAY) < CURDATE()
                    #     HAVING total_outstanding > 0 AND overdue > 0
                    #     """, (cust.name, company), as_dict=1)
                    
                    # if outstanding:
                    #     # frappe.log_error(outstanding,"Try to create outstanding")
                    #     filters = frappe._dict(
                    #         {
                    #             "company": company,
                    #             "customer": cust.name,
                    #             "customer Name": cust.customer_name,
                    #             "as on Date" : frappe.utils.today(),
                    #             "Total Outstanding": outstanding[0].total_outstanding
                    #         }
                    #     )
                    #     report_data = frappe.desk.query_report.run(
                    #         "Customer Due 150 Days",
                    #         filters=filters
                    #     )


                    #     letter_head = frappe.get_doc('Letter Head', 'geolife')
                    #     total=0.00
                    #     if report_data["result"]:
                    #         max_len= len(report_data["result"])
                    #         last_index= max_len-1
                    #         del report_data["result"][last_index]
                            
                    #         # frappe.log_error(len(report_data["result"]),"count try out loop")

                    #         for clm in report_data["result"]:
                    #             total= total + clm['outstanding']

                               
                    #     if total >0:
                    #         # frappe.log_error( total,"try total outstanding on report")

                    #         html = frappe.render_template('templates/CustomerDue150Days.html',
                    #             {
                    #                 "filters": filters,
                    #                 "data": report_data["result"],
                    #                 "title": "Customer Due 150 Days",
                    #                 "columns": report_data["columns"],
                    #                 "letter_head": letter_head
                    #             }
                    #         )
                    #         # frappe.log_error(filters,"Try to create filters")
                    #         # frappe.log_error(report_data,"Try to create outstanding")
                    #         # frappe.log_error(html,"Try to create html")

                    #         html = frappe.render_template('frappe/www/printview.html',
                    #             { "body": html, "css": get_print_style(), "title": "Customer Due 150 Days"}
                    #         )

                    #         # send_whatsapp_report(html, "Customer Due 150 Days", cust.customer_primary_contact, "150days", outstanding, cust.name, cust.customer_name )
                    #         # send_whatsapp_report(html, "Customer Due 150 Days", cust.mobile_no, "150days", outstanding, cust.name, cust.customer_name, total )
                    #         frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_whatsapp_report", html=html, document_caption="Customer Due 150 Days", contact=cust.mobile_no, wa_template="150days",outstanding=outstanding, party=cust.customer_name, party_name=cust.name, total=total)

                    #         # frappe.log_error(cust,"whatsapp Sent to ")
                    #         # cdoc= frappe.get_doc({
                    #         #     'doctype': 'Geolife Whatsapp Log',
                    #         #     'party': cust.name,
                    #         #     'mobile': cust.mobile_no,
                    #         #     'template': "150days",
                    #         #     # 'request': str(payload),
                    #         #     'customer':cust.name,
                    #         #     # 'response': str(response)
                    #         #     # 'wa_id': response.contacts[0].wa_id if response else "",
                    #         #     # 'message_id': response.messages[0].id if response else "",
                    #         #     # 'message_status': response.messages[0].message_status
                    #         # }).insert()
                    #         # frappe.log_error(cdoc, "try Customer")


                    #         current_cust = frappe.get_doc("Customer",cust.name)
                    #         if current_cust.sales_team:
                    #             sales_person_exits= frappe.db.exists("Sales Person", current_cust.sales_team[0].sales_person)
                    #             if sales_person_exits :
                    #                 sales_person = frappe.get_doc("Sales Person", current_cust.sales_team[0].sales_person)
                    #                 if sales_person.mobile_no :
                    #                     if int(sales_person.mobile_no) > 6200000000:
                    #                         # not_sended_customers.append(cust.name)
                    #                         # mdoc =frappe.get_doc({
                    #                         #     'doctype': 'Geolife Whatsapp Log',
                    #                         #     'party': sales_person.name,
                    #                         #     'mobile': sales_person.mobile_no,
                    #                         #     'template': "150days",
                    #                         #     # 'request': str(payload),
                    #                         #     'customer':cust.name,
                    #                         #     # 'response': str(response)
                    #                         #     # 'wa_id': response.contacts[0].wa_id if response else "",
                    #                         #     # 'message_id': response.messages[0].id if response else "",
                    #                         #     # 'message_status': response.messages[0].message_status
                    #                         # }).insert()
                    #                         # frappe.log_error(mdoc, "try sales man")
                    #                         # send_whatsapp_report(html, "Customer Due 150 Days", sales_person.mobile_no, "150days", outstanding, sales_person.first_name, cust.name, total )
                    #                         frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_whatsapp_report", html=html, document_caption="Customer Due 150 Days", contact=sales_person.mobile_no, wa_template="150days",outstanding=outstanding, party=sales_person.first_name, party_name=cust.name, total=total)
                    #         # send_cash_discount_whatsapp_report(html, "Cash Discount", cust.customer_primary_contact, "cash_discount")party=sales_person.first_name, customer=cust.name, contact=sales_person.mobile_no,
                    #     else:
                    #         frappe.log_error( total,"try total outstanding on report")


                    #     doc = frappe.get_doc("Customer", cust.name)
                    #     doc.add_comment("Comment", text=f"WHATSAPP for Account Block Notification Sent On {cust.mobile_no}")
                    # else:
                    #     frappe.log_error(cust,"Outstanding Not found")

    except Exception as e:
        frappe.log_error(e, "whatsapp_for_account_block_log")
        # if e =="Task exceeded maximum timeout value (300 seconds)":
        #     send_account_block_whatsapp()

def cusutomer_enqueue_send_account_block_whatsapp(cust):
    try:
        company = 'Geolife Agritech India Private Limited'
        if cust.mobile_no:
            frappe.log_error(cust,"Try to Send 150")
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
                # frappe.log_error(outstanding,"Try to create outstanding")
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
                total=0.00
                if report_data["result"]:
                    max_len= len(report_data["result"])
                    last_index= max_len-1
                    del report_data["result"][last_index]
                    
                    # frappe.log_error(len(report_data["result"]),"count try out loop")
                    for clm in report_data["result"]:
                        total= total + clm['outstanding']

                if total >0:
                    # frappe.log_error( total,"try total outstanding on report")
                    html = frappe.render_template('templates/CustomerDue150Days.html',
                        {
                            "filters": filters,
                            "data": report_data["result"],
                            "title": "Customer Due 150 Days",
                            "columns": report_data["columns"],
                            "letter_head": letter_head
                        }
                    )
                    # frappe.log_error(filters,"Try to create filters")
                    # frappe.log_error(report_data,"Try to create outstanding")
                    # frappe.log_error(html,"Try to create html")
                    html = frappe.render_template('frappe/www/printview.html',
                        { "body": html, "css": get_print_style(), "title": "Customer Due 150 Days"}
                    )

                    frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_whatsapp_report", html=html, document_caption="Customer Due 150 Days", contact=cust.mobile_no, wa_template="150days",outstanding=outstanding, party=cust.customer_name, party_name=cust.name, total=total)
                    current_cust = frappe.get_doc("Customer",cust.name)
                    # if current_cust.sales_team:
                    #     sales_person_exits= frappe.db.exists("Sales Person", current_cust.sales_team[0].sales_person)
                    #     if sales_person_exits :
                    #         sales_person = frappe.get_doc("Sales Person", current_cust.sales_team[0].sales_person)
                    #         if sales_person.mobile_no :
                    #             if int(sales_person.mobile_no) > 6200000000:
                    #                 frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_whatsapp_report", html=html, document_caption="Customer Due 150 Days", contact=sales_person.mobile_no, wa_template="150days",outstanding=outstanding, party=sales_person.first_name, party_name=cust.name, total=total)
                    if current_cust.sales_person:
                        emp_exits= frappe.db.exists("Employee", current_cust.sales_person)
                        if emp_exits :
                            emp = frappe.get_doc("Employee", current_cust.sales_person)
                            if emp.cug_no :
                                if int(emp.cug_no) > 6200000000:
                                    frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_whatsapp_report", html=html, document_caption="Customer Due 150 Days", contact=emp.cug_no, wa_template="150days",outstanding=outstanding, party=emp.employee_name, party_name=cust.name, total=total)
                    if current_cust.area_manager:
                            emp_exits1= frappe.db.exists("Employee", current_cust.area_manager)
                            if emp_exits1 :
                                emp1 = frappe.get_doc("Employee", current_cust.area_manager)
                                if emp1.cug_no :
                                    if int(emp1.cug_no) > 6200000000:
                                        frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_whatsapp_report", html=html, document_caption="Customer Due 150 Days", contact=emp1.cug_no, wa_template="150days",outstanding=outstanding, party=emp1.employee_name, party_name=cust.name, total=total)
                    if current_cust.regional_manager:
                            emp_exits2= frappe.db.exists("Employee", current_cust.regional_manager)
                            if emp_exits2 :
                                emp2 = frappe.get_doc("Employee", current_cust.regional_manager)
                                if emp2.cug_no :
                                    if int(emp2.cug_no) > 6200000000:
                                        frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_whatsapp_report", html=html, document_caption="Customer Due 150 Days", contact=emp2.cug_no, wa_template="150days",outstanding=outstanding, party=emp2.employee_name, party_name=cust.name, total=total)
                
                else:
                    frappe.log_error( total,"try total outstanding on report")


                doc = frappe.get_doc("Customer", cust.name)
                doc.add_comment("Comment", text=f"WHATSAPP for Account Block Notification Sent On {cust.mobile_no}")
            else:
                frappe.log_error(cust,"Outstanding Not found")
    except Exception as e:
        frappe.log_error(e,'cusutomer_enqueue_send_account_block_whatsapp')


def send_whatsapp_report(html, document_caption, contact, wa_template, outstanding, party, party_name, total):
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
        # receiver = frappe.db.get_value("Contact", contact, "mobile_no")
        receiver = contact
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
                                "text": str(total)
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
        frappe.get_doc({
            'doctype': 'Geolife Whatsapp Log',
            'party': party,
            'mobile': receiver,
            'template': wa_template,
            'request': str(payload),
            'customer':party_name,
            'response': str(response)
            # 'wa_id': response.contacts[0].wa_id if response else "",
            # 'message_id': response.messages[0].id if response else "",
            # 'message_status': response.messages[0].message_status
            }).insert()
        # frappe.log_error(f"req = {str(payload)} Resp = {str(response)}",wa_template)
        frappe.msgprint("Whatsapp Sent")

    except Exception as e:
        frappe.log_error(f"error = {str(e)}")

def send_cash_discount_whatsapp():

    send_whatsapp_for_cash_discount = frappe.db.get_single_value("Geolife Settings", "send_whatsapp_for_cash_discount")
    
    if send_whatsapp_for_cash_discount == 0:
        return
    
    try:
        customers = frappe.db.sql("SELECT name, mobile_no, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no <> '' and branch not in ('Amazon', 'Karnataka Factory', 'Factory', 'Head Office','ECOM MH','ECOM KRT') and customer_active_type not in ('Closed')", as_dict=1)
        # customers = frappe.db.sql("SELECT name, mobile_no, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no='9604035386' and branch not in ('Amazon', 'Karnataka Factory', 'Factory', 'Head Office') and customer_active_type not in ('Closed')", as_dict=1)
        company = 'Geolife Agritech India Private Limited'
        sended_whatsapp_customers_list = [d.customer for d in frappe.db.get_all("Geolife Whatsapp Log",filters={'posting_date':frappe.utils.nowdate(), 'template':'cash_discount'}, fields=["customer"])]  

        frappe.log_error(customers,'send customers')
        for cust in customers:
            if cust.name not in sended_whatsapp_customers_list:
                frappe.enqueue(customer_send_cash_discount_whatsapp,queue="long", cust=cust)

                # if cust.mobile_no :
                #     result = []
                #     total_cd_amount = 0
                #     bills = frappe.db.sql("""
                #          SELECT 
                #             a.customer as party,
                #             a.posting_date,a.effective_date, IF(a.effective_date != '', a.effective_date, a.posting_date) as EffectiveDate,
                #             DATE_ADD(IF(a.effective_date != '', a.effective_date, a.posting_date), INTERVAL 120 DAY) due_date,
                #             a.name as reference_no,
                #             (a.grand_total + a.rounding_adjustment) as opening_amount,
                #             (a.grand_total + a.rounding_adjustment) - a.outstanding_amount as receipt_amount,
                #             a.outstanding_amount as closing_amount,
                #             -- DATEDIFF(CURDATE(), DATE_ADD(IF(effective_date != '', effective_date, posting_date), INTERVAL 120 DAY)) due_days,
                #             "" due_days,
                #             a.status,
                #             0 cd_percent,
                #             0 cd_amount,
                #             0 sales_return,
                #             0 adjustments,
                #             0 cheque_return,
                #             0 payments,
                #             "" due_days_for_cd,
                #             "" cd_opportunity,
                #             "Sales" type,
                #             a.scheme_applicable
                #         FROM
                #             `tabSales Invoice` a
                #         WHERE
                #             a.customer = %s AND a.company = %s
                #             AND a.docstatus = 1
                #             AND a.is_return = 0
                #             AND a.outstanding_amount > 0
                #              -- AND a.scheme_applicable in ('Diwali Bonus Scheme 23-24', 'Rabi Season Lifiting Scheme For FY 2023-24 MP', 'Vigore Rabi Scheme for FY 2023-24 (MP)', 'Nanofert and Nanomeal Series Scheme For FY 2023-24', 'Vigore Scheme 2023-24 for WB', 'Geomycin Scheme for 2023-24 for WB', 'Vigore Scheme for Rabi Season 23-24 (KRT-TN)', 'Tabsil FGO Scheme 23-24 (MH2)', 'Add on scheme No Virus 2023-24 (KRT,TN)', 'Advance Booking Lifting Scheme Sep 2023 (KRT,TN)', 'Gold Offer on Bactogang+Carbon Stone 23-24 (KRT & TN)', 'Geomycin Scheme 2023-24 (CEZ+BH)', 'Lifting Scheme for Category A (except Vigore) 23-24 (NZ+NCZ)', 'Vigore Rabi Scheme 23-24 (NZ+NCZ)', 'Ultramax Scheme 23-24 All India', 'Cylinder Scheme 23-24 MH2', 'Cylinder & Plus or Salute Scheme 23-24 MH2', 'Vigore Dhamaka Scheme 23-24 MH2', 'Geomycin Scheme 23-24 (Sep-2023) KRT and TN', 'Plus Grapes Scheme 23-24 MH 2', 'Foundation Scheme 23-24 MH 2', 'Geomycin Scheme 23-24 (Aug-Sep 2023) KRT & TN', 'Geomycin Scheme 23-24 (Aug-Sep 2023) NZ+NCZ', 'Vigore dhamaka Scheme 23-24 for MH2 (5Kg-50Kg slab added as per internal approval)', 'Advance Booking Lifting Scheme August 2023 (AP, KRT, TN, WB & Patna) 1', 'Jodi No.1 Scheme 23-24 MH2', 'Cylinder Scheme 23-24 (MH2)', 'Gold Offer on Vigore 23-24 TN', 'Add on Scheme for Bactogang,Tabsil (FA), Geomycin, Nano Vigore, Change 23-24', 'Plus FGO Scheme 23-24 MH2', 'Salute FGO Scheme 23-24 MH2', 'Vigore Lifting Scheme  23-24 (CZ,CEZ,NZ,NCZ) (extended till 16.8.23)', 'Vigore Sale Dhamaka Scheme for 17th July To 16th Aug (CZ, CEZ, NZ, NCZ,WB)', 'Plus Booking Scheme 2023-24 (All India)', 'Advance Booking & Lifting Discount Scheme for July 2023 (AP, KRT, TN, WB & Patna)', 'Annual Disc Scheme 23-24 MH2', 'Coupon Scheme 23-24 MH 2', 'Cylinder & Plus Scheme 23-24 MH 2', 'Ultramax Dhamaka Offer 23-24 MH2', 'Geomycin Scheme 23-24', 'Advance Booking Lifting Scheme July 2023', 'Advance Booking Lifting Scheme June 2023', 'Small Pack Gift Scheme 23-24', 'Vigore Lifting Scheme  23-24', 'Mitti Ka Shringar 23-24 KRT', 'Mitti Ka Shringar 23-24', 'Advance Booking Lifting Scheme May 2023', 'Bactogang Seed Scheme 23-24', 'Georrhiza Scheme 23-24', 'Cylinder Scheme 23-24', 'Pesticides Scheme 23-24', 'Plus Kharif Booking Scheme 23-24', 'Jodi No 1 Scheme 23-24', 'Ultramax Discount Scheme 23-24 MH-2', 'Category B Sale 23-24', 'Spider Scheme 23-24', 'Ultramax Discount Scheme 23-24', 'Annual Discount Scheme 23-24', 'Advance Booking Lifting Scheme April 2023', 'Vigore Rabi Scheme FY 23-24 (CEZ+BIH)', 'Vigore FS Scheme 23-24', 'Postbox Scheme 23-24', 'Bactogang 24 Launching Offer 23-24', 'Annual Disc Scheme 24-25 All India', 'Advance Booking & Lifting Discount Scheme for Apr+May'2024', 'Spider Discount Scheme 2024-25', 'Jodi No 1 Scheme 24-25 All India', 'Ultramax Discount Scheme 24-25 (NZ+NCZ)', 'Vigore Scheme  24-25 (All India)', 'Vigore FGO Scheme 24-25')
                #         ORDER BY a.effective_date
                #     """, (cust.name, company), as_dict=1)

                #     if bills:
                #         for bill in bills:

                #             due_days = frappe.utils.date_diff(frappe.utils.today(), bill["EffectiveDate"])  or 0
                #             cd_schemes = [
                #                 'Diwali Bonus Scheme 23-24',
                #                 'Rabi Season Lifiting Scheme For FY 2023-24 MP',
                #                 'Vigore Rabi Scheme for FY 2023-24 (MP)',
                #                 'Nanofert and Nanomeal Series Scheme For FY 2023-24',
                #                 'Vigore Scheme 2023-24 for WB',
                #                 'Geomycin Scheme for 2023-24 for WB',
                #                 'Vigore Scheme for Rabi Season 23-24 (KRT-TN)',
                #                 'Tabsil FGO Scheme 23-24 (MH2)',
                #                 'Add on scheme No Virus 2023-24 (KRT,TN)',
                #                 'Advance Booking Lifting Scheme Sep 2023 (KRT,TN)',
                #                 'Gold Offer on Bactogang+Carbon Stone 23-24 (KRT & TN)',
                #                 'Geomycin Scheme 2023-24 (CEZ+BH)',
                #                 'Lifting Scheme for Category A (except Vigore) 23-24 (NZ+NCZ)',
                #                 'Vigore Rabi Scheme 23-24 (NZ+NCZ)',
                #                 'Ultramax Scheme 23-24 All India',
                #                 'Cylinder Scheme 23-24 MH2',
                #                 'Cylinder & Plus or Salute Scheme 23-24 MH2',
                #                 'Vigore Dhamaka Scheme 23-24 MH2',
                #                 'Geomycin Scheme 23-24 (Sep-2023) KRT and TN',
                #                 'Plus Grapes Scheme 23-24 MH 2',
                #                 'Foundation Scheme 23-24 MH 2',
                #                 'Geomycin Scheme 23-24 (Aug-Sep 2023) KRT & TN',
                #                 'Geomycin Scheme 23-24 (Aug-Sep 2023) NZ+NCZ',
                #                 'Vigore dhamaka Scheme 23-24 for MH2 (5Kg-50Kg slab added as per internal approval)',
                #                 'Advance Booking Lifting Scheme August 2023 (AP, KRT, TN, WB & Patna) 1',
                #                 'Jodi No.1 Scheme 23-24 MH2',
                #                 'Cylinder Scheme 23-24 (MH2)',
                #                 'Gold Offer on Vigore 23-24 TN',
                #                 'Add on Scheme for Bactogang,Tabsil (FA), Geomycin, Nano Vigore, Change 23-24',
                #                 'Plus FGO Scheme 23-24 MH2',
                #                 'Salute FGO Scheme 23-24 MH2',
                #                 'Vigore Lifting Scheme  23-24 (CZ,CEZ,NZ,NCZ) (extended till 16.8.23)',
                #                 'Vigore Sale Dhamaka Scheme for 17th July To 16th Aug (CZ, CEZ, NZ, NCZ,WB)',
                #                 'Plus Booking Scheme 2023-24 (All India)',
                #                 'Advance Booking & Lifting Discount Scheme for July 2023 (AP, KRT, TN, WB & Patna)',
                #                 'Annual Disc Scheme 23-24 MH2',
                #                 'Coupon Scheme 23-24 MH 2',
                #                 'Cylinder & Plus Scheme 23-24 MH 2',
                #                 'Ultramax Dhamaka Offer 23-24 MH2',
                #                 'Geomycin Scheme 23-24',
                #                 'Advance Booking Lifting Scheme July 2023',
                #                 'Advance Booking Lifting Scheme June 2023',
                #                 'Small Pack Gift Scheme 23-24',
                #                 'Vigore Lifting Scheme  23-24',
                #                 'Mitti Ka Shringar 23-24 KRT',
                #                 'Mitti Ka Shringar 23-24',
                #                 'Advance Booking Lifting Scheme May 2023',
                #                 'Bactogang Seed Scheme 23-24',
                #                 'Georrhiza Scheme 23-24',
                #                 'Cylinder Scheme 23-24',
                #                 'Pesticides Scheme 23-24',
                #                 'Plus Kharif Booking Scheme 23-24',
                #                 'Jodi No 1 Scheme 23-24',
                #                 'Ultramax Discount Scheme 23-24 MH-2',
                #                 'Category B Sale 23-24',
                #                 'Spider Scheme 23-24',
                #                 'Ultramax Discount Scheme 23-24',
                #                 "Annual Discount Scheme 23-24",
                #                 'Advance Booking Lifting Scheme April 2023',
                #                 'Vigore Rabi Scheme FY 23-24 (CEZ+BIH)',
                #                 'Vigore FS Scheme 23-24',
                #                 'Postbox Scheme 23-24',
                #                 'Bactogang 24 Launching Offer 23-24',
                #                 "Annual Disc Scheme 24-25 All India",
                #                 'Advance Booking & Lifting Discount Scheme for Apr+May\'2024',
                #                 "Spider Discount Scheme 2024-25",
                #                 "Jodi No 1 Scheme 24-25 All India",
                #                 "Ultramax Discount Scheme 24-25 (NZ+NCZ)",
                #                 "Vigore Scheme  24-25 (All India)",
                #                 "Chaitra Dhamaka Offer 24-25 (Solapur)",
                #                 "Advance Booking & Lifting Discount Scheme for April'24 (South Zone)",
                #                 "Ultramax Discount Scheme 24-25 (NZ+NCZ)",
                #                 "Advance Booking & Lifting Discount Scheme for May'24 (South Zone)",
                #                 "Bactogang Seed Treatment Scheme 24-25 All India",
                #                 "Georrhiza Scheme 24-25 All India",
                #                 "Tabsil FA Scheme 24-25 All India",
                #                 "Vigore FGO Scheme 24-25"
                #             ]

                #             if bill.get("scheme_applicable") in cd_schemes:
                #                 bill["due_days"] = due_days or 0
                                
                #                 x = frappe.db.sql("""
                #                     SELECT percent, to_days from `tabETPL Product Group CD` where parent = 'All Items Group' AND 
                #                     %s BETWEEN applicable_from AND applicable_to AND %s BETWEEN from_days AND to_days
                #                 """, (bill["EffectiveDate"], due_days), as_dict=1)
                            
                #                 if x:
                #                     cd_per = x[0].percent or 0
                #                     to_days = x[0].to_days or 0
                #                     due_days = bill["due_days"] or 0
                #                     bill["cd_percent"] = f"{cd_per} %"
                #                     bill["due_days"] = f"{due_days} "
                #                     bill["cd_amount"] = round((bill["closing_amount"] * cd_per) / 100)
                #                     bill["cd_opportunity"] = (bill["closing_amount"] * 9) / 100
                #                     bill["cd_loss"] = bill["cd_opportunity"] - bill["cd_amount"]
                #                     bill["valid_upto"] = frappe.utils.add_to_date(bill["EffectiveDate"], days=to_days) 
                            
                #                 else:
                #                     bill["cd_percent"] = f" 0 %"
                #                     due_days = bill["due_days"] or 0
                #                     bill["due_days"] = f"{due_days} "
                #                     bill["valid_upto"] = "NA"
                #             else:
                #                 #due_days = bill["due_days"] or 0
                #                 bill["cd_percent"] = f"0 %"
                #                 bill["due_days"] = f"{due_days} "
                #                 bill["valid_upto"] = "NA"
                #             result.append(bill)
                            
                #             eligible_schemes = [
                #                 'Diwali Bonus Scheme 23-24',
                #                 'Nanofert and Nanomeal Series Scheme For FY 2023-24',
                #                 'Vigore Dhamaka Scheme 23-24 MH2',
                #                 'Geomycin Scheme 23-24 (Sep-2023) KRT and TN', 'Geomycin Scheme 23-24 (Aug-Sep 2023) KRT & TN',
                #                 'Vigore dhamaka Scheme 23-24 for MH2 (5Kg-50Kg slab added as per internal approval)',
                #                 'Advance Booking Lifting Scheme August 2023 (AP, KRT, TN, WB & Patna) 1', 'Cylinder Scheme 23-24 (MH2)',
                #                 'Gold Offer on Vigore 23-24 TN', 'Vigore Sale Dhamaka Scheme for 17th July To 16th Aug (CZ, CEZ, NZ, NCZ,WB)',
                #                 'Coupon Scheme 23-24 MH 2', 'Cylinder & Plus Scheme 23-24 MH 2', 'Ultramax Dhamaka Offer 23-24 MH2',
                #                 'Small Pack Gift Scheme 23-24', 'Mitti Ka Shringar 23-24', 'Pesticides Scheme 23-24',
                #                 'Plus Kharif Booking Scheme 23-24', 'Jodi No 1 Scheme 23-24', 'Category B Sale 23-24', 'Spider Scheme 23-24',
                #                 'Annual Discount Scheme 23-24', 'Advance Booking Lifting Scheme April 2023',
                #                 'Vigore Rabi Scheme FY 23-24 (CEZ+BIH)', 'Bactogang 24 Launching Offer 23-24',
                #                 'Annual Disc Scheme 24-25 All India', 'Advance Booking & Lifting Discount Scheme for Apr+May\'2024',
                #                 'Chaitra Dhamaka Offer 24-25 (Solapur)',
                #                 "Advance Booking & Lifting Discount Scheme for April'24 (South Zone)",
                #                 "Advance Booking & Lifting Discount Scheme for May'24 (South Zone)",
                #                 "Tabsil FA Scheme 24-25 All India",
                #                 "Vigore FGO Scheme 24-25"
                #             ]

                #             if due_days <= 150 and bill.get("scheme_applicable") in eligible_schemes:
                #                 bill["due_days"] = due_days or 0
                #                 # Calculate and add the additional 5% discount
                #                 bill["cd_amount_with_5_percent_discount"] = (bill["closing_amount"] * 5) / 100
                                
                #             else:
                #                 # If not eligible for the extra discount, set the new column value to the original cash discount amount
                #                 bill["cd_amount_with_5_percent_discount"] = 0
                #                 bill["due_days"] = due_days or 0
                                
                #             if int(bill['due_days']) > 150:
                #                 bill['cd_percent'] = '*'
                            

                #             bill["total_discount"] = bill["cd_amount"] + bill["cd_amount_with_5_percent_discount"]
                #             result.append(bill)

                #         # add total row
                #         total_cd_amount = 0
                #         for t in result:
                #             if t.get("type") == "Sales":
                #                 total_cd_amount = total_cd_amount + t.get("cd_amount") or 0
                #     opening_amount = 0
                #     closing_amount = 0
                #     cd_amount = 0
                #     cd_amount_with_5_percent_discount = 0
                #     total_discount = 0
                #     for t in result:
                #         opening_amount = opening_amount + t.get("opening_amount") or 0
                #         closing_amount = closing_amount + t.get("closing_amount")
                #         cd_amount = cd_amount + t.get("cd_amount")
                #         cd_amount_with_5_percent_discount = cd_amount_with_5_percent_discount + t.get("cd_amount_with_5_percent_discount")
                #         total_discount = total_discount + t.get("total_discount") or 0

                #     result.append({"opening_amount": opening_amount, "closing_amount": closing_amount, "cd_amount": cd_amount, "cd_amount_with_5_percent_discount": cd_amount_with_5_percent_discount, "total_discount": total_discount})    
                #     frappe.log_error(result,'send customers')


                #     if total_cd_amount > 0:

                #         filters = frappe._dict(
                #             {
                #                 "company": company,
                #                 "customer": cust.name,
                #                 "Customer Name": frappe.db.get_value("Customer", cust.name, "customer_name"),
                #                 "Report Date" : frappe.utils.today(),
                #                 "": "Bill wise summary showing the cash discount & Timely Payment Received Discount on your outstanding invoices.<br><b>NOTE:</b><br>1. Cash Discount / Invoice Clearance Discount amount can be reduce/change as per scheme Credit Note applicable as per invoice.<br>2. Excess Payment made due to CN will be adjust in next invoice and CD will applicable on that invoice.<br>3. Payment received are consider as FIFO basis for CD Benifits.<br>4.* Account Block due to overdue invoice more than 151 Days."

                #             }
                #         )
                #         report_data = frappe.desk.query_report.run(
                #             "Cash Discount & Timely Payment Received Discount Statement",
                #             filters=filters
                #         )

                #         letter_head = frappe.get_doc('Letter Head', 'geolife')

                #         html = frappe.render_template('templates/CashDiscountDistributor.html',
                #             {
                #                 "filters": filters,
                #                 "data": report_data["result"],
                #                 "title": "Cash Discount & Timely Payment Received Discount Statement",
                #                 "columns": report_data["columns"],
                #                 "letter_head": letter_head
                #             }
                #         )

                #         html = frappe.render_template('frappe/www/printview.html',
                #             { "body": html, "css": get_print_style(), "title": "Cash Discount & Timely Payment Received Discount Statement"}
                #         )
                #         frappe.log_error(total_cd_amount,'send customers')
                #         frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_cash_discount_whatsapp_report", html=html, document_caption="Cash Discount", contact=cust.mobile_no, wa_template="cash_and_timely_payment_discount", party=cust.name, customer=cust.name)
                #         current_cust = frappe.get_doc("Customer",cust.name)
                #         if current_cust.sales_team:
                #             sales_person_exits= frappe.db.exists("Sales Person", current_cust.sales_team[0].sales_person)
                #             if sales_person_exits :
                #                 sales_person = frappe.get_doc("Sales Person", current_cust.sales_team[0].sales_person)
                #                 if sales_person.mobile_no :
                #                     if int(sales_person.mobile_no) > 6200000000:
                #                         # not_sended_customers.append(cust.name)
                #                         frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_cash_discount_whatsapp_report", html=html, document_caption="Cash Discount", contact=sales_person.mobile_no, wa_template="cash_and_timely_payment_discount", party=sales_person.first_name, customer=cust.name)
                #         # send_cash_discount_whatsapp_report(html, "Cash Discount", cust.customer_primary_contact, "cash_discount")party=sales_person.first_name, customer=cust.name, contact=sales_person.mobile_no,

                #         doc = frappe.get_doc("Customer", cust.name)
                #         doc.add_comment("Comment", text=f"WHATSAPP for Cash Discount Sent On {cust.mobile_no}")
                #     else:
                #         frappe.log_error(cust,'customer cash dishcount not found')


                    
    except Exception as e:
        frappe.log_error(e, "whatsapp_for_cash_discount_log")

def customer_send_cash_discount_whatsapp(cust):
    
    company = 'Geolife Agritech India Private Limited'
    if cust.mobile_no :
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
                    -- AND a.scheme_applicable in ('Diwali Bonus Scheme 23-24', 'Rabi Season Lifiting Scheme For FY 2023-24 MP', 'Vigore Rabi Scheme for FY 2023-24 (MP)', 'Nanofert and Nanomeal Series Scheme For FY 2023-24', 'Vigore Scheme 2023-24 for WB', 'Geomycin Scheme for 2023-24 for WB', 'Vigore Scheme for Rabi Season 23-24 (KRT-TN)', 'Tabsil FGO Scheme 23-24 (MH2)', 'Add on scheme No Virus 2023-24 (KRT,TN)', 'Advance Booking Lifting Scheme Sep 2023 (KRT,TN)', 'Gold Offer on Bactogang+Carbon Stone 23-24 (KRT & TN)', 'Geomycin Scheme 2023-24 (CEZ+BH)', 'Lifting Scheme for Category A (except Vigore) 23-24 (NZ+NCZ)', 'Vigore Rabi Scheme 23-24 (NZ+NCZ)', 'Ultramax Scheme 23-24 All India', 'Cylinder Scheme 23-24 MH2', 'Cylinder & Plus or Salute Scheme 23-24 MH2', 'Vigore Dhamaka Scheme 23-24 MH2', 'Geomycin Scheme 23-24 (Sep-2023) KRT and TN', 'Plus Grapes Scheme 23-24 MH 2', 'Foundation Scheme 23-24 MH 2', 'Geomycin Scheme 23-24 (Aug-Sep 2023) KRT & TN', 'Geomycin Scheme 23-24 (Aug-Sep 2023) NZ+NCZ', 'Vigore dhamaka Scheme 23-24 for MH2 (5Kg-50Kg slab added as per internal approval)', 'Advance Booking Lifting Scheme August 2023 (AP, KRT, TN, WB & Patna) 1', 'Jodi No.1 Scheme 23-24 MH2', 'Cylinder Scheme 23-24 (MH2)', 'Gold Offer on Vigore 23-24 TN', 'Add on Scheme for Bactogang,Tabsil (FA), Geomycin, Nano Vigore, Change 23-24', 'Plus FGO Scheme 23-24 MH2', 'Salute FGO Scheme 23-24 MH2', 'Vigore Lifting Scheme  23-24 (CZ,CEZ,NZ,NCZ) (extended till 16.8.23)', 'Vigore Sale Dhamaka Scheme for 17th July To 16th Aug (CZ, CEZ, NZ, NCZ,WB)', 'Plus Booking Scheme 2023-24 (All India)', 'Advance Booking & Lifting Discount Scheme for July 2023 (AP, KRT, TN, WB & Patna)', 'Annual Disc Scheme 23-24 MH2', 'Coupon Scheme 23-24 MH 2', 'Cylinder & Plus Scheme 23-24 MH 2', 'Ultramax Dhamaka Offer 23-24 MH2', 'Geomycin Scheme 23-24', 'Advance Booking Lifting Scheme July 2023', 'Advance Booking Lifting Scheme June 2023', 'Small Pack Gift Scheme 23-24', 'Vigore Lifting Scheme  23-24', 'Mitti Ka Shringar 23-24 KRT', 'Mitti Ka Shringar 23-24', 'Advance Booking Lifting Scheme May 2023', 'Bactogang Seed Scheme 23-24', 'Georrhiza Scheme 23-24', 'Cylinder Scheme 23-24', 'Pesticides Scheme 23-24', 'Plus Kharif Booking Scheme 23-24', 'Jodi No 1 Scheme 23-24', 'Ultramax Discount Scheme 23-24 MH-2', 'Category B Sale 23-24', 'Spider Scheme 23-24', 'Ultramax Discount Scheme 23-24', 'Annual Discount Scheme 23-24', 'Advance Booking Lifting Scheme April 2023', 'Vigore Rabi Scheme FY 23-24 (CEZ+BIH)', 'Vigore FS Scheme 23-24', 'Postbox Scheme 23-24', 'Bactogang 24 Launching Offer 23-24', 'Annual Disc Scheme 24-25 All India', 'Advance Booking & Lifting Discount Scheme for Apr+May'2024', 'Spider Discount Scheme 2024-25', 'Jodi No 1 Scheme 24-25 All India', 'Ultramax Discount Scheme 24-25 (NZ+NCZ)', 'Vigore Scheme  24-25 (All India)', 'Vigore FGO Scheme 24-25')
            ORDER BY a.effective_date
        """, (cust.name, company), as_dict=1)

        if bills:
            for bill in bills:

                due_days = frappe.utils.date_diff(frappe.utils.today(), bill["EffectiveDate"])  or 0
                cd_schemes_list = frappe.db.sql("""
                    SELECT
                        name
                    FROM
                        `tabGeolife Scheme` gs
                    WHERE
                        %s BETWEEN scheme_valid_from AND scheme_valid_to
                        AND cd_applicable = 1
                """, (bill["EffectiveDate"]), as_dict=True)

                cd_schemes = [x["name"] for x in cd_schemes_list]
                
                if bill.get("scheme_applicable") in cd_schemes:
                    bill["due_days"] = due_days or 0
                    
                    x = frappe.db.sql("""
                        SELECT percent, to_days from `tabETPL Product Group CD` where parent = 'All Items Group' AND 
                        %s BETWEEN applicable_from AND applicable_to AND %s BETWEEN from_days AND to_days
                    """, (bill["EffectiveDate"], due_days), as_dict=1)
                
                    if x:
                        cd_per = x[0].percent or 0
                        to_days = x[0].to_days or 0
                        due_days = bill["due_days"] or 0
                        bill["cd_percent"] = f"{cd_per} %"
                        bill["due_days"] = f"{due_days} "
                        bill["cd_amount"] = round((bill["closing_amount"] * cd_per) / 100)
                        bill["cd_opportunity"] = (bill["closing_amount"] * 9) / 100
                        bill["cd_loss"] = bill["cd_opportunity"] - bill["cd_amount"]
                        bill["valid_upto"] = frappe.utils.add_to_date(bill["EffectiveDate"], days=to_days) 
                
                    else:
                        bill["cd_percent"] = f" 0 %"
                        due_days = bill["due_days"] or 0
                        bill["due_days"] = f"{due_days} "
                        bill["valid_upto"] = "NA"
                else:
                    #due_days = bill["due_days"] or 0
                    bill["cd_percent"] = f"0 %"
                    bill["due_days"] = f"{due_days} "
                    bill["valid_upto"] = "NA"
                result.append(bill)
                
                eligible_schemes_list = frappe.db.sql("""
                    SELECT
                        name
                    FROM
                        `tabGeolife Scheme` gs
                    WHERE
                        %s BETWEEN scheme_valid_from AND scheme_valid_to
                        AND sdc_applicable = 1
                """, (bill["EffectiveDate"]), as_dict=True)
                
                eligible_schemes = [x["name"] for x in eligible_schemes_list]

                if due_days <= 150 and bill.get("scheme_applicable") in eligible_schemes:
                    bill["due_days"] = due_days or 0
                    # Calculate and add the additional 5% discount
                    bill["cd_amount_with_5_percent_discount"] = (bill["closing_amount"] * 5) / 100
                    
                else:
                    # If not eligible for the extra discount, set the new column value to the original cash discount amount
                    bill["cd_amount_with_5_percent_discount"] = 0
                    bill["due_days"] = due_days or 0
                    
                if int(bill['due_days']) > 150:
                    bill['cd_percent'] = '*'
                

                bill["total_discount"] = bill["cd_amount"] + bill["cd_amount_with_5_percent_discount"]
                result.append(bill)

            # add total row
            total_cd_amount = 0
            for t in result:
                if t.get("type") == "Sales":
                    total_cd_amount = total_cd_amount + t.get("cd_amount") or 0
        opening_amount = 0
        closing_amount = 0
        cd_amount = 0
        cd_amount_with_5_percent_discount = 0
        total_discount = 0
        for t in result:
            opening_amount = opening_amount + t.get("opening_amount") or 0
            closing_amount = closing_amount + t.get("closing_amount")
            cd_amount = cd_amount + t.get("cd_amount")
            cd_amount_with_5_percent_discount = cd_amount_with_5_percent_discount + t.get("cd_amount_with_5_percent_discount")
            total_discount = total_discount + t.get("total_discount") or 0

        result.append({"opening_amount": opening_amount, "closing_amount": closing_amount, "cd_amount": cd_amount, "cd_amount_with_5_percent_discount": cd_amount_with_5_percent_discount, "total_discount": total_discount})    
        frappe.log_error(result,'send customers')


        if total_cd_amount > 0:

            filters = frappe._dict(
                {
                    "company": company,
                    "customer": cust.name,
                    "Customer Name": frappe.db.get_value("Customer", cust.name, "customer_name"),
                    "Report Date" : frappe.utils.today(),
                    "": "Bill wise summary showing the cash discount & Timely Payment Received Discount on your outstanding invoices.<br><b>NOTE:</b><br>1. Cash Discount / Invoice Clearance Discount amount can be reduce/change as per scheme Credit Note applicable as per invoice.<br>2. Excess Payment made due to CN will be adjust in next invoice and CD will applicable on that invoice.<br>3. Payment received are consider as FIFO basis for CD Benifits.<br>4.* Account Block due to overdue invoice more than 151 Days."

                }
            )
            report_data = frappe.desk.query_report.run(
                "Cash Discount & Timely Payment Received Discount Statement",
                filters=filters
            )

            letter_head = frappe.get_doc('Letter Head', 'geolife')

            html = frappe.render_template('templates/CashDiscountDistributor.html',
                {
                    "filters": filters,
                    "data": report_data["result"],
                    "title": "Cash Discount & Timely Payment Received Discount Statement",
                    "columns": report_data["columns"],
                    "letter_head": letter_head
                }
            )

            html = frappe.render_template('frappe/www/printview.html',
                { "body": html, "css": get_print_style(), "title": "Cash Discount & Timely Payment Received Discount Statement"}
            )
            frappe.log_error(total_cd_amount,'send customers')
            frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_cash_discount_whatsapp_report", html=html, document_caption="Cash Discount", contact=cust.mobile_no, wa_template="cash_and_timely_payment_discount", party=cust.name, customer=cust.name)
            current_cust = frappe.get_doc("Customer",cust.name)
            # if current_cust.sales_team:
            #     sales_person_exits= frappe.db.exists("Sales Person", current_cust.sales_team[0].sales_person)
            #     if sales_person_exits :
            #         sales_person = frappe.get_doc("Sales Person", current_cust.sales_team[0].sales_person)
            #         if sales_person.mobile_no :
            #             if int(sales_person.mobile_no) > 6200000000:
            #                 # not_sended_customers.append(cust.name)
            #                 frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_cash_discount_whatsapp_report", html=html, document_caption="Cash Discount", contact=sales_person.mobile_no, wa_template="cash_and_timely_payment_discount", party=sales_person.first_name, customer=cust.name)
            if current_cust.sales_person:
                    emp_exits= frappe.db.exists("Employee", current_cust.sales_person)
                    if emp_exits :
                        emp = frappe.get_doc("Employee", current_cust.sales_person)
                        if emp.cug_no :
                            if int(emp.cug_no) > 6200000000:
                                frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_cash_discount_whatsapp_report", html=html, document_caption="Cash Discount", contact=emp.cug_no, wa_template="cash_and_timely_payment_discount", party=cust.name, customer=cust.name)
            if current_cust.area_manager:
                    emp_exits1= frappe.db.exists("Employee", current_cust.area_manager)
                    if emp_exits1 :
                        emp1 = frappe.get_doc("Employee", current_cust.area_manager)
                        if emp1.cug_no :
                            if int(emp1.cug_no) > 6200000000:
                                frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_cash_discount_whatsapp_report", html=html, document_caption="Cash Discount", contact=emp1.cug_no, wa_template="cash_and_timely_payment_discount", party=cust.name, customer=cust.name)
            if current_cust.regional_manager:
                    emp_exits2= frappe.db.exists("Employee", current_cust.regional_manager)
                    if emp_exits2 :
                        emp2 = frappe.get_doc("Employee", current_cust.regional_manager)
                        if emp2.cug_no :
                            if int(emp2.cug_no) > 6200000000:
                                frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_cash_discount_whatsapp_report", html=html, document_caption="Cash Discount", contact=emp2.cug_no, wa_template="cash_and_timely_payment_discount", party=cust.name, customer=cust.name)
            
            
            
            
            
            
            
            
            
            
            # send_cash_discount_whatsapp_report(html, "Cash Discount", cust.customer_primary_contact, "cash_discount")party=sales_person.first_name, customer=cust.name, contact=sales_person.mobile_no,

            doc = frappe.get_doc("Customer", cust.name)
            doc.add_comment("Comment", text=f"WHATSAPP for Cash Discount Sent On {cust.mobile_no}")
        else:
            frappe.log_error(cust,'customer cash dishcount not found')




def send_cash_discount_whatsapp_report(html, document_caption, contact, wa_template, party, customer):
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
        # receiver = frappe.db.get_value("Contact", contact, "mobile_no")
        receiver = contact
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
        frappe.get_doc({
            'doctype': 'Geolife Whatsapp Log',
            'party': party,
            'mobile': contact,
            'template': wa_template,
            'request': str(payload),
            'customer':customer,
            'response': str(response)
            # 'wa_id': response.contacts[0].wa_id if response else "",
            # 'message_id': response.messages[0].id if response else "",
            # 'message_status': response.messages[0].message_status
            }).insert()
        # frappe.log_error(f"req = {str(payload)} Resp = {str(response)}",wa_template)
        frappe.msgprint("Whatsapp Sent")

    except Exception as e:
        frappe.log_error(f"error = {str(e)}")


def enqueue_send_ledger_whatsapp():
    try:
        customers = frappe.db.sql("SELECT name, customer_name, mobile_no, customer_primary_contact from tabCustomer where name='FAC-CUST-0458'and mobile_no is not null and mobile_no <> '' and branch not in ('Amazon', 'Head Office','ECOM MH','ECOM KRT') and customer_active_type in ('Active', 'Overdue')", as_dict=1)
        # customers = frappe.db.sql("SELECT name, customer_name, mobile_no, customer_primary_contact from tabCustomer where mobile_no is not null and mobile_no <> '' and branch not in ('Amazon', 'Karnataka Factory', 'Factory', 'Head Office') and customer_active_type in ('Active', 'Overdue')", as_dict=1)
        # customers = frappe.db.sql("SELECT name, customer_name, mobile_no, customer_primary_contact from tabCustomer where mobile_no in ('9604035386') and customer_active_type in ('Active', 'Overdue')", as_dict=1)
        company = 'Geolife Agritech India Private Limited'
        
        sended_whatsapp_customers_list = [d.customer for d in frappe.db.get_all("Geolife Whatsapp Salesman Log",filters={'posting_date':frappe.utils.nowdate(), 'template':'ledger_statement_by_date'}, fields=["customer"])]  
        not_sended_customers =[]   
        # frappe.log_error(customers,'Sended Customers')
        
        for cust in customers:
            if cust.name not in sended_whatsapp_customers_list:
                current_cust = frappe.get_doc("Customer",cust.name)
                # if current_cust.sales_team:
                #     sales_person_exits= frappe.db.exists("Sales Person", current_cust.sales_team[0].sales_person)
                #     if sales_person_exits :
                #         sales_person = frappe.get_doc("Sales Person", current_cust.sales_team[0].sales_person)
                #         if sales_person.mobile_no :
                #             if int(sales_person.mobile_no) > 6200000000:
                not_sended_customers.append(cust.name)
                if cust.get("mobile_no"):
                    filters = frappe._dict(
                        {
                            "company": company,
                            "from_date": "2023-04-01",
                            "to_date": str(frappe.utils.get_last_day(frappe.utils.add_months(frappe.utils.today(), -1))),
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
                    frappe.log_error(report_data,'report_data Sended Customers')

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

                    # if cust.name not in sended_whatsapp_customers_list:
                        # current_cust = frappe.get_doc("Customer",cust.name)
                        # if current_cust.sales_team:
                        #     sales_person = frappe.get_doc("Sales Person", current_cust.sales_team[0].sales_person)
                        #     if sales_person.mobile_no:
                                # frappe.log_error(sales_person,"sales_person Whatsapp")
                                # frappe.get_doc({
                                #     'doctype': 'Geolife Whatsapp Salesman Log',
                                #     'party': sales_person.first_name,
                                #     'mobile': sales_person.mobile_no,
                                #     'template': "ledger_statement_by_date",
                                #     # 'request': str(payload),
                                #     # 'response': str(response)
                                #     # 'wa_id': response.contacts[0].wa_id if response else "",
                                #     # 'message_id': response.messages[0].id if response else "",
                                #     # 'message_status': response.messages[0].message_status
                                #     }).insert()
                    # frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_ledger_whatsapp_report",queue='long', html=html, document_caption="Statement of Accounts", contact=sales_person.mobile_no, wa_template="ledger_statement_by_date", from_date=filters.get("from_date"), to_date=filters.get("to_date"), party=sales_person.first_name, customer=cust.name)
                    # else :
                        # pass
                    frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_ledger_whatsapp_report",queue='long', html=html, document_caption="Statement of Accounts", contact=cust.mobile_no, wa_template="ledger_statement_by_date", from_date=filters.get("from_date"), to_date=filters.get("to_date"), party=cust.name, customer=cust.name)

                    if current_cust.sales_person:
                        emp_exits= frappe.db.exists("Employee", current_cust.sales_person)
                        if emp_exits :
                            emp = frappe.get_doc("Employee", current_cust.sales_person)
                            if emp.cug_no :
                                if int(emp.cug_no) > 6200000000:
                                    frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_ledger_whatsapp_report",queue='long', html=html, document_caption="Statement of Accounts", contact=emp.cug_no, wa_template="ledger_statement_by_date", from_date=filters.get("from_date"), to_date=filters.get("to_date"), party=emp.employee_name, customer=cust.name)
                    if current_cust.area_manager:
                            emp_exits1= frappe.db.exists("Employee", current_cust.area_manager)
                            if emp_exits1 :
                                emp1 = frappe.get_doc("Employee", current_cust.area_manager)
                                if emp1.cug_no :
                                    if int(emp1.cug_no) > 6200000000:
                                        frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_ledger_whatsapp_report",queue='long', html=html, document_caption="Statement of Accounts", contact=emp1.cug_no, wa_template="ledger_statement_by_date", from_date=filters.get("from_date"), to_date=filters.get("to_date"), party=emp1.employee_name, customer=cust.name)
                    if current_cust.regional_manager:
                            emp_exits2= frappe.db.exists("Employee", current_cust.regional_manager)
                            if emp_exits2 :
                                emp2 = frappe.get_doc("Employee", current_cust.regional_manager)
                                if emp2.cug_no :
                                    if int(emp2.cug_no) > 6200000000:
                                        frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_ledger_whatsapp_report",queue='long', html=html, document_caption="Statement of Accounts", contact=emp2.cug_no, wa_template="ledger_statement_by_date", from_date=filters.get("from_date"), to_date=filters.get("to_date"), party=emp2.employee_name, customer=cust.name)
                





                    #send_ledger_whatsapp_report(html, "Statement of Accounts", cust.customer_primary_contact, "ledger_statement_by_date", filters.get("from_date"), filters.get("to_date"))

                    #doc = frappe.get_doc("Customer", cust.name)
                    #doc.add_comment("Comment", text=f"WHATSAPP for Ledger Sent On {cust.mobile_no}")
        
        # frappe.log_error(not_sended_customers,'Not Sended Customers')
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "whatsapp_for_ledger_log")



def send_ledger_whatsapp():

    send_whatsapp_for_ledger = frappe.db.get_single_value("Geolife Settings", "send_whatsapp_for_ledger")
    
    if send_whatsapp_for_ledger == 0:
        return
    frappe.enqueue(enqueue_send_ledger_whatsapp, queue="long")


def send_ledger_whatsapp_report(html, document_caption, contact, wa_template, from_date, to_date, party,customer):
    # frappe.log_error(party,'Send party')
    # frappe.log_error(contact,'Send party')
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
        # receiver = frappe.db.get_value("Contact", contact, "mobile_no")
        # if not receiver:
        #     frappe.throw("Mobile Number Not Specified")

        file_path = frappe.utils.get_files_path(saved_file.file_name)

        while not os.path.exists(file_path):
            time.sleep(1)

        payload = json.dumps({
            "messaging_product": "whatsapp",
            "to": contact,
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

        response = make_post_request(base_url, headers=headers, data=payload)

        frappe.get_doc({
            'doctype': 'Geolife Whatsapp Salesman Log',
            'party': party,
            'mobile': contact,
            'template': wa_template,
            'request': str(payload),
            'customer':customer,
            'response': str(response)
            # 'wa_id': response.contacts[0].wa_id if response else "",
            # 'message_id': response.messages[0].id if response else "",
            # 'message_status': response.messages[0].message_status
            }).insert()
        # frappe.log_error(f"Req = {str(payload)} Resp = {str(response)}", "whatsapp_for_ledger")
        frappe.log_error(payload,"Whatsapp Sent to Salesman")

    except Exception as e:
        frappe.log_error(payload,f"error = {str(e)}")

        
@frappe.whitelist()
def send_stock_balance_automail_whatsapp_for_sales_person():
#     send_whatsapp_for_ledger = frappe.db.get_single_value("Geolife Settings", "send_whatsapp_for_ledger")
#     if send_whatsapp_for_ledger == 0:
#         return
    try:
        employees = frappe.db.get_all("Employee", filters=[["Employee Warehouses","warehouse","is","set"],["Employee","status","=","Active"],["Employee","cug_no","is","set"]], fields=["name"], group_by="name")
        company = 'Geolife Agritech India Private Limited'
        frappe.log_error(employees, "employee list")

        for emp in employees:
            employee = frappe.get_doc("Employee", emp.get('name'))
            warehouses= [ d.get('warehouse') for d in employee.get('employee_warehouses') ]
            frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_stock_balance_automail_report_whatsapp_for_sales_person",queue='long', contact=employee.get('cug_no'), party=employee.get('name'), warehouses=warehouses)
                    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "whatsapp_for_ledger_log")


def send_stock_balance_automail_report_whatsapp_for_sales_person(contact, party, warehouses):
        try:
            for wrh in warehouses:
                filters = frappe._dict(
                    {"company":"Geolife Agritech India Private Limited",
                        "from_date":frappe.utils.today(),
                        "to_date":frappe.utils.today(),
                        "warehouse":wrh
                        }
                )
                report_data = frappe.desk.query_report.run(
                    "Stock Balance - Automail",
                    filters=filters,
                    ignore_prepared_report=True
                )

                # report = frappe.get_doc("Report","Stock Balance - Automail")

                # columns, data = report.get_data(
                #     filters=filters,
                #     as_dict=True,
                #     ignore_prepared_report=True
                # )





                # frappe.log_error(columns, "columns list")
                frappe.log_error(report_data, "report_data list")
                report_data["result"].pop()

                letter_head = frappe.get_doc('Letter Head', 'geolife')

                html = frappe.render_template('templates/StockBalance.html',
                    {
                        "filters": filters,
                        "data": report_data["result"],
                        "title": "Stock Balance - Automail",
                        "columns": report_data["columns"],
                        "letter_head": letter_head,
                        "terms_and_conditions": False,
                        "ageing": False,
                    }
                )

                html = frappe.render_template('frappe/www/printview.html',
                    { "body": html, "css": get_print_style(), "title": "Stock Balance - Automail"}
                )
                frappe.log_error('entered in enqueue', "enqueue list")

                frappe.enqueue("geolife_customapp.geolife_customapp.whatsapp.send_report_auto_mail_whatsapp_report",queue='long', html=html, document_caption="Stock Balance - Automail", contact=contact, wa_template="stock_balance_1", party=party, warehouse=wrh )

        except Exception as e:
            frappe.log_error(e,"send_stock_ balance_automail_report_whatsapp_for_sales_person")

def send_report_auto_mail_whatsapp_report(html, document_caption, contact, wa_template, party, warehouse):
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
        # receiver = frappe.db.get_value("Contact", contact, "mobile_no")
        # if not receiver:
        #     frappe.throw("Mobile Number Not Specified")

        file_path = frappe.utils.get_files_path(saved_file.file_name)

        while not os.path.exists(file_path):
            time.sleep(1)

        payload = json.dumps({
            "messaging_product": "whatsapp",
            "to": contact,
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
                                    "filename": f"{warehouse} {document_caption}"
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

        response = make_post_request(base_url, headers=headers, data=payload)

        frappe.get_doc({
            'doctype': 'Geolife Whatsapp Salesman Log',
            'party': party,
            'mobile': contact,
            'template': wa_template,
            'request': str(payload),
            # 'customer':customer,
            'response': str(response)
            }).insert()
        # frappe.log_error(f"Req = {str(payload)} Resp = {str(response)}", "whatsapp_for_ledger")
        frappe.log_error(payload,"Whatsapp Sent to Salesman")

    except Exception as e:
        frappe.log_error(payload,f"error = {str(e)}")

