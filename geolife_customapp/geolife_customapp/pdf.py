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
from frappe.utils.pdf import get_pdf



@frappe.whitelist()
def dealer_outstanding_pdf(customer):
    
    filters = frappe._dict(
        {
            "company": "Geolife Agritech India Private Limited",
            "customer": customer,
            "customer Name": frappe.db.get_value("Customer", customer, "customer_name"),
            "as on Date" : frappe.utils.today(),
            "Total Outstanding": ""
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

    pdf_data = get_pdf(html)
    unique_hash = frappe.generate_hash()[:10]
    s_file_name = f"{unique_hash}.pdf"
    folder_name = create_folder("Whatsapp", "Home")
    saved_file = save_file(s_file_name, pdf_data, '', '', folder=folder_name, is_private=0)
    s_document_link = f"{frappe.utils.get_url()}/files/{saved_file.file_name}"

    return s_document_link


@frappe.whitelist()
def get_general_ledger_pdf(customer, from_date, to_date):
    try:
        
        filters = frappe._dict(
            {
                "company": "Geolife Agritech India Private Limited",
                "from_date": from_date,
                "to_date": to_date,
                "account":[],
                "party_type": "Customer",
                "party": [customer],
                "party_name": frappe.db.get_value("Customer", customer, "customer_name"),
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

        pdf_data = get_pdf(html)
        unique_hash = frappe.generate_hash()[:10]
        s_file_name = f"{unique_hash}.pdf"
        folder_name = create_folder("Whatsapp", "Home")
        saved_file = save_file(s_file_name, pdf_data, '', '', folder=folder_name, is_private=0)
        s_document_link = f"{frappe.utils.get_url()}/files/{saved_file.file_name}"

        return s_document_link
    except Exception as e:
        return e



@frappe.whitelist()
def get_confirmation_of_accounts_pdf(customer, from_date, to_date):
    
    filters = frappe._dict(
        {
            "company": "Geolife Agritech India Private Limited",
            "from_date": from_date,
            "to_date": to_date,
            "account":[],
            "party_type": "Customer",
            "party": [customer],
            "party_name": frappe.db.get_value("Customer", customer, "customer_name"),
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

    html = frappe.render_template('templates/ConfirmationofAccounts.html',
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
        { "body": html, "css": get_print_style(), "title": "Confimration of Accounts"}
    )

    pdf_data = get_pdf(html)
    unique_hash = frappe.generate_hash()[:10]
    s_file_name = f"{unique_hash}.pdf"
    folder_name = create_folder("Whatsapp", "Home")
    saved_file = save_file(s_file_name, pdf_data, '', '', folder=folder_name, is_private=0)
    s_document_link = f"{frappe.utils.get_url()}/files/{saved_file.file_name}"

    return s_document_link