# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
import frappe.defaults
from frappe.utils import cint, flt, add_months, today, date_diff, getdate, add_days, cstr, nowdate
from frappe import _, msgprint, throw
from erpnext.accounts.party import get_party_account, get_due_date
from erpnext.controllers.stock_controller import update_gl_entries_after
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.doctype.sales_invoice.pos import update_multi_mode_option

from erpnext.controllers.selling_controller import SellingController
from erpnext.accounts.utils import get_account_currency
from erpnext.stock.doctype.delivery_note.delivery_note import update_billed_amount_based_on_so
from erpnext.projects.doctype.timesheet.timesheet import get_projectwise_timesheet_data
from erpnext.assets.doctype.asset.depreciation \
    import get_disposal_account_and_cost_center, get_gl_entries_on_asset_disposal
from erpnext.stock.doctype.batch.batch import set_batch_nos
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos, get_delivery_note_serial_no
from erpnext.setup.doctype.company.company import update_company_current_month_sales
from erpnext.accounts.general_ledger import get_round_off_account_and_cost_center
from erpnext.accounts.doctype.loyalty_program.loyalty_program import \
    get_loyalty_program_details_with_points, get_loyalty_details, validate_loyalty_points
from erpnext.accounts.deferred_revenue import validate_service_stop_date

from erpnext.healthcare.utils import manage_invoice_submit_cancel

from six import iteritems

form_grid_templates = {
    "items": "templates/form_grid/item_grid.html"
}

class AkontoInvoice(SellingController):
    def __init__(self, *args, **kwargs):
        super(AkontoInvoice, self).__init__(*args, **kwargs)
        self.status_updater = [{
            'source_dt': 'Akonto Invoice Item',
            'target_field': 'billed_amt',
            'target_ref_field': 'amount',
            'target_dt': 'Sales Order Item',
            'join_field': 'so_detail',
            'target_parent_dt': 'Sales Order',
            'target_parent_field': 'per_billed',
            'source_field': 'amount',
            'join_field': 'so_detail',
            'percent_join_field': 'sales_order',
            'status_field': 'billing_status',
            'keyword': 'Billed',
            'overflow_type': 'billing'
        }]

    def get_akonto_item(self):
        return frappe.get_value("Heim Settings", "Heim Settings", "akonto_item")
        
    def set_indicator(self):
        """Set indicator for portal"""
        if self.outstanding_amount < 0:
            self.indicator_title = _("Credit Note Issued")
            self.indicator_color = "darkgrey"
        elif self.outstanding_amount > 0 and getdate(self.due_date) >= getdate(nowdate()):
            self.indicator_color = "orange"
            self.indicator_title = _("Unpaid")
        elif self.outstanding_amount > 0 and getdate(self.due_date) < getdate(nowdate()):
            self.indicator_color = "red"
            self.indicator_title = _("Overdue")
        elif cint(self.is_return) == 1:
            self.indicator_title = _("Return")
            self.indicator_color = "darkgrey"
        else:
            self.indicator_color = "green"
            self.indicator_title = _("Paid")

    def validate(self):
        super(AkontoInvoice, self).validate()
        self.validate_auto_set_posting_time()

        self.validate_proj_cust()
        self.validate_with_previous_doc()
        self.validate_uom_is_integer("stock_uom", "stock_qty")
        self.validate_uom_is_integer("uom", "qty")
        self.check_sales_order_on_hold_or_close("sales_order")
        self.add_remarks()

        self.validate_multiple_billing("Delivery Note", "dn_detail", "amount", "items")
        self.set_status()

    def on_submit(self):
        self.check_prev_docstatus()

        # this sequence because outstanding may get -ve
        #self.make_gl_entries()

    def on_cancel(self):
        super(AkontoInvoice, self).on_cancel()

        self.check_sales_order_on_hold_or_close("sales_order")

        self.update_prevdoc_status()

        #self.make_gl_entries_on_cancel()
        frappe.db.set(self, 'status', 'Cancelled')

        unlink_inter_company_doc(self.doctype, self.name, self.inter_company_invoice_reference)

    def check_credit_limit(self):
        from erpnext.selling.doctype.customer.customer import check_credit_limit

        validate_against_credit_limit = False
        bypass_credit_limit_check_at_sales_order = frappe.db.get_value("Customer Credit Limit",
            filters={'parent': self.customer, 'parenttype': 'Customer', 'company': self.company},
            fieldname=["bypass_credit_limit_check"])

        if bypass_credit_limit_check_at_sales_order:
            validate_against_credit_limit = True

        for d in self.get("items"):
            if not (d.sales_order or d.delivery_note):
                validate_against_credit_limit = True
                break
        if validate_against_credit_limit:
            check_credit_limit(self.customer, self.company, bypass_credit_limit_check_at_sales_order)

    def set_missing_values(self, for_validate=False):
        if not self.due_date and self.customer:
            self.due_date = get_due_date(self.posting_date, "Customer", self.customer, self.company)

        super(AkontoInvoice, self).set_missing_values(for_validate)
        return

    def update_time_sheet(self, sales_invoice):
        for d in self.timesheets:
            if d.time_sheet:
                timesheet = frappe.get_doc("Timesheet", d.time_sheet)
                self.update_time_sheet_detail(timesheet, d, sales_invoice)
                timesheet.calculate_total_amounts()
                timesheet.calculate_percentage_billed()
                timesheet.flags.ignore_validate_update_after_submit = True
                timesheet.set_status()
                timesheet.save()

    def update_time_sheet_detail(self, timesheet, args, sales_invoice):
        for data in timesheet.time_logs:
            if (self.project and args.timesheet_detail == data.name) or \
                (not self.project and not data.sales_invoice) or \
                (not sales_invoice and data.sales_invoice == self.name):
                data.sales_invoice = sales_invoice

    def validate_time_sheets_are_submitted(self):
        for data in self.timesheets:
            if data.time_sheet:
                status = frappe.db.get_value("Timesheet", data.time_sheet, "status")
                if status not in ['Submitted', 'Payslip']:
                    frappe.throw(_("Timesheet {0} is already completed or cancelled").format(data.time_sheet))

    def get_company_abbr(self):
        return frappe.db.sql("select abbr from tabCompany where name=%s", self.company)[0][0]

    def validate_with_previous_doc(self):
        super(AkontoInvoice, self).validate_with_previous_doc({
            "Sales Order": {
                "ref_dn_field": "sales_order",
                "compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]]
            },
            "Sales Order Item": {
                "ref_dn_field": "so_detail",
                "compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
                "is_child_table": True,
                "allow_duplicate_prev_row_id": True
            },
            "Delivery Note": {
                "ref_dn_field": "delivery_note",
                "compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]]
            },
            "Delivery Note Item": {
                "ref_dn_field": "dn_detail",
                "compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
                "is_child_table": True,
                "allow_duplicate_prev_row_id": True
            },
        })

        if cint(frappe.db.get_single_value('Selling Settings', 'maintain_same_sales_rate')) and not self.is_return:
            self.validate_rate_with_reference_doc([
                ["Sales Order", "sales_order", "so_detail"],
                ["Delivery Note", "delivery_note", "dn_detail"]
            ])

    def add_remarks(self):
        if not self.remarks: self.remarks = 'No Remarks'

    def validate_auto_set_posting_time(self):
        # Don't auto set the posting date and time if invoice is amended
        if self.is_new() and self.amended_from:
            self.set_posting_time = 1

        self.validate_posting_time()

    def so_dn_required(self):
        """check in manage account if sales order / delivery note required or not."""
        if self.is_return:
            return
        dic = {'Sales Order':['so_required', 'is_pos'],'Delivery Note':['dn_required', 'update_stock']}
        for i in dic:
            if frappe.db.get_single_value('Selling Settings', dic[i][0]) == 'Yes':
                for d in self.get('items'):
                    is_stock_item = frappe.get_cached_value('Item', d.item_code, 'is_stock_item')
                    if  (d.item_code and is_stock_item == 1\
                        and not d.get(i.lower().replace(' ','_')) and not self.get(dic[i][1])):
                        msgprint(_("{0} is mandatory for Item {1}").format(i,d.item_code), raise_exception=1)


    def validate_proj_cust(self):
        """check for does customer belong to same project as entered.."""
        if self.project and self.customer:
            res = frappe.db.sql("""select name from `tabProject`
                where name = %s and (customer = %s or customer is null or customer = '')""",
                (self.project, self.customer))
            if not res:
                throw(_("Customer {0} does not belong to project {1}").format(self.customer,self.project))

    def validate_item_code(self):
        for d in self.get('items'):
            if not d.item_code:
                msgprint(_("Item Code required at Row No {0}").format(d.idx), raise_exception=True)

    def validate_warehouse(self):
        super(SalesInvoice, self).validate_warehouse()

        for d in self.get_item_list():
            if not d.warehouse and frappe.get_cached_value("Item", d.item_code, "is_stock_item"):
                frappe.throw(_("Warehouse required for stock Item {0}").format(d.item_code))

    def validate_delivery_note(self):
        for d in self.get("items"):
            if d.delivery_note:
                msgprint(_("Stock cannot be updated against Delivery Note {0}").format(d.delivery_note), raise_exception=1)

    def validate_dropship_item(self):
        for item in self.items:
            if item.sales_order:
                if frappe.db.get_value("Sales Order Item", item.so_detail, "delivered_by_supplier"):
                    frappe.throw(_("Could not update stock, invoice contains drop shipping item."))

    def update_current_stock(self):
        for d in self.get('items'):
            if d.item_code and d.warehouse:
                bin = frappe.db.sql("select actual_qty from `tabBin` where item_code = %s and warehouse = %s", (d.item_code, d.warehouse), as_dict = 1)
                d.actual_qty = bin and flt(bin[0]['actual_qty']) or 0

        for d in self.get('packed_items'):
            bin = frappe.db.sql("select actual_qty, projected_qty from `tabBin` where item_code =    %s and warehouse = %s", (d.item_code, d.warehouse), as_dict = 1)
            d.actual_qty = bin and flt(bin[0]['actual_qty']) or 0
            d.projected_qty = bin and flt(bin[0]['projected_qty']) or 0

    def update_packing_list(self):
        if cint(self.update_stock) == 1:
            from erpnext.stock.doctype.packed_item.packed_item import make_packing_list
            make_packing_list(self)
        else:
            self.set('packed_items', [])

    def set_billing_hours_and_amount(self):
        if not self.project:
            for timesheet in self.timesheets:
                ts_doc = frappe.get_doc('Timesheet', timesheet.time_sheet)
                if not timesheet.billing_hours and ts_doc.total_billable_hours:
                    timesheet.billing_hours = ts_doc.total_billable_hours

                if not timesheet.billing_amount and ts_doc.total_billable_amount:
                    timesheet.billing_amount = ts_doc.total_billable_amount

    def update_timesheet_billing_for_project(self):
        if not self.timesheets and self.project:
            self.add_timesheet_data()
        else:
            self.calculate_billing_amount_for_timesheet()

    def add_timesheet_data(self):
        self.set('timesheets', [])
        if self.project:
            for data in get_projectwise_timesheet_data(self.project):
                self.append('timesheets', {
                        'time_sheet': data.parent,
                        'billing_hours': data.billing_hours,
                        'billing_amount': data.billing_amt,
                        'timesheet_detail': data.name
                    })

            self.calculate_billing_amount_for_timesheet()

    def calculate_billing_amount_for_timesheet(self):
        total_billing_amount = 0.0
        for data in self.timesheets:
            if data.billing_amount:
                total_billing_amount += data.billing_amount

        self.total_billing_amount = total_billing_amount

    def get_warehouse(self):
        user_pos_profile = frappe.db.sql("""select name, warehouse from `tabPOS Profile`
            where ifnull(user,'') = %s and company = %s""", (frappe.session['user'], self.company))
        warehouse = user_pos_profile[0][1] if user_pos_profile else None

        if not warehouse:
            global_pos_profile = frappe.db.sql("""select name, warehouse from `tabPOS Profile`
                where (user is null or user = '') and company = %s""", self.company)

            if global_pos_profile:
                warehouse = global_pos_profile[0][1]
            elif not user_pos_profile:
                msgprint(_("POS Profile required to make POS Entry"), raise_exception=True)

        return warehouse

    def check_prev_docstatus(self):
        for d in self.get('items'):
            if d.sales_order and frappe.db.get_value("Sales Order", d.sales_order, "docstatus") != 1:
                frappe.throw(_("Sales Order {0} is not submitted").format(d.sales_order))

            if d.delivery_note and frappe.db.get_value("Delivery Note", d.delivery_note, "docstatus") != 1:
                throw(_("Delivery Note {0} is not submitted").format(d.delivery_note))

    def make_gl_entries(self, gl_entries=None, repost_future_gle=True, from_repost=False):
        auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)

        if not gl_entries:
            gl_entries = self.get_gl_entries()

        if gl_entries:
            from erpnext.accounts.general_ledger import make_gl_entries

            # if POS and amount is written off, updating outstanding amt after posting all gl entries
            update_outstanding = "No" if (cint(self.is_pos) or self.write_off_account or
                cint(self.redeem_loyalty_points)) else "Yes"

            make_gl_entries(gl_entries, cancel=(self.docstatus == 2),
                update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)

            if update_outstanding == "No":
                from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
                update_outstanding_amt(self.debit_to, "Customer", self.customer,
                    self.doctype, self.return_against if cint(self.is_return) and self.return_against else self.name)

            if repost_future_gle and cint(self.update_stock) \
                and cint(auto_accounting_for_stock):
                    items, warehouses = self.get_items_and_warehouses()
                    update_gl_entries_after(self.posting_date, self.posting_time,
                        warehouses, items, company = self.company)
        elif self.docstatus == 2 and cint(self.update_stock) \
            and cint(auto_accounting_for_stock):
                from erpnext.accounts.general_ledger import delete_gl_entries
                delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

    def get_gl_entries(self, warehouse_account=None):
        from erpnext.accounts.general_ledger import merge_similar_entries

        gl_entries = []

        self.make_customer_gl_entry(gl_entries)

        self.make_tax_gl_entries(gl_entries)

        self.make_item_gl_entries(gl_entries)

        # merge gl entries before adding pos entries
        gl_entries = merge_similar_entries(gl_entries)

        self.make_loyalty_point_redemption_gle(gl_entries)
        self.make_pos_gl_entries(gl_entries)
        self.make_gle_for_change_amount(gl_entries)

        self.make_write_off_gl_entry(gl_entries)
        self.make_gle_for_rounding_adjustment(gl_entries)

        return gl_entries

    def make_customer_gl_entry(self, gl_entries):
        # Checked both rounding_adjustment and rounded_total
        # because rounded_total had value even before introcution of posting GLE based on rounded total
        grand_total = self.rounded_total if (self.rounding_adjustment and self.rounded_total) else self.grand_total
        if grand_total:
            # Didnot use base_grand_total to book rounding loss gle
            grand_total_in_company_currency = flt(grand_total * self.conversion_rate,
                self.precision("grand_total"))

            gl_entries.append(
                self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "due_date": self.due_date,
                    "against": self.against_income_account,
                    "debit": grand_total_in_company_currency,
                    "debit_in_account_currency": grand_total_in_company_currency \
                        if self.party_account_currency==self.company_currency else grand_total,
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center
                }, self.party_account_currency)
            )

    def make_tax_gl_entries(self, gl_entries):
        for tax in self.get("taxes"):
            if flt(tax.base_tax_amount_after_discount_amount):
                account_currency = get_account_currency(tax.account_head)
                gl_entries.append(
                    self.get_gl_dict({
                        "account": tax.account_head,
                        "against": self.customer,
                        "credit": flt(tax.base_tax_amount_after_discount_amount,
                            tax.precision("tax_amount_after_discount_amount")),
                        "credit_in_account_currency": (flt(tax.base_tax_amount_after_discount_amount,
                            tax.precision("base_tax_amount_after_discount_amount")) if account_currency==self.company_currency else
                            flt(tax.tax_amount_after_discount_amount, tax.precision("tax_amount_after_discount_amount"))),
                        "cost_center": tax.cost_center
                    }, account_currency)
                )

    def make_item_gl_entries(self, gl_entries):
        # income account gl entries
        for item in self.get("items"):
            if flt(item.base_net_amount, item.precision("base_net_amount")):
                if item.is_fixed_asset:
                    asset = frappe.get_doc("Asset", item.asset)

                    if (len(asset.finance_books) > 1 and not item.finance_book
                        and asset.finance_books[0].finance_book):
                        frappe.throw(_("Select finance book for the item {0} at row {1}")
                            .format(item.item_code, item.idx))

                    fixed_asset_gl_entries = get_gl_entries_on_asset_disposal(asset,
                        item.base_net_amount, item.finance_book)

                    for gle in fixed_asset_gl_entries:
                        gle["against"] = self.customer
                        gl_entries.append(self.get_gl_dict(gle))

                    asset.db_set("disposal_date", self.posting_date)
                    asset.set_status("Sold" if self.docstatus==1 else None)
                else:
                    income_account = (item.income_account
                        if (not item.enable_deferred_revenue or self.is_return) else item.deferred_revenue_account)

                    account_currency = get_account_currency(income_account)
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": income_account,
                            "against": self.customer,
                            "credit": flt(item.base_net_amount, item.precision("base_net_amount")),
                            "credit_in_account_currency": (flt(item.base_net_amount, item.precision("base_net_amount"))
                                if account_currency==self.company_currency
                                else flt(item.net_amount, item.precision("net_amount"))),
                            "cost_center": item.cost_center
                        }, account_currency, item=item)
                    )

        # expense account gl entries
        if cint(self.update_stock) and \
            erpnext.is_perpetual_inventory_enabled(self.company):
            gl_entries += super(SalesInvoice, self).get_gl_entries()

    def make_loyalty_point_redemption_gle(self, gl_entries):
        if cint(self.redeem_loyalty_points):
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": "Expense account - " + cstr(self.loyalty_redemption_account) + " for the Loyalty Program",
                    "credit": self.loyalty_amount,
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center
                })
            )
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.loyalty_redemption_account,
                    "cost_center": self.cost_center or self.loyalty_redemption_cost_center,
                    "against": self.customer,
                    "debit": self.loyalty_amount,
                    "remark": "Loyalty Points redeemed by the customer"
                })
            )

    def make_pos_gl_entries(self, gl_entries):
        if cint(self.is_pos):
            for payment_mode in self.payments:
                if payment_mode.amount:
                    # POS, make payment entries
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": self.debit_to,
                            "party_type": "Customer",
                            "party": self.customer,
                            "against": payment_mode.account,
                            "credit": payment_mode.base_amount,
                            "credit_in_account_currency": payment_mode.base_amount \
                                if self.party_account_currency==self.company_currency \
                                else payment_mode.amount,
                            "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                            "against_voucher_type": self.doctype,
                            "cost_center": self.cost_center
                        }, self.party_account_currency)
                    )

                    payment_mode_account_currency = get_account_currency(payment_mode.account)
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": payment_mode.account,
                            "against": self.customer,
                            "debit": payment_mode.base_amount,
                            "debit_in_account_currency": payment_mode.base_amount \
                                if payment_mode_account_currency==self.company_currency \
                                else payment_mode.amount,
                            "cost_center": self.cost_center
                        }, payment_mode_account_currency)
                    )

    def make_gle_for_change_amount(self, gl_entries):
        if cint(self.is_pos) and self.change_amount:
            if self.account_for_change_amount:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.debit_to,
                        "party_type": "Customer",
                        "party": self.customer,
                        "against": self.account_for_change_amount,
                        "debit": flt(self.base_change_amount),
                        "debit_in_account_currency": flt(self.base_change_amount) \
                            if self.party_account_currency==self.company_currency else flt(self.change_amount),
                        "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                        "against_voucher_type": self.doctype,
                        "cost_center": self.cost_center
                    }, self.party_account_currency)
                )

                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.account_for_change_amount,
                        "against": self.customer,
                        "credit": self.base_change_amount,
                        "cost_center": self.cost_center
                    })
                )
            else:
                frappe.throw(_("Select change amount account"), title="Mandatory Field")

    def make_write_off_gl_entry(self, gl_entries):
        # write off entries, applicable if only pos
        if self.write_off_account and flt(self.write_off_amount, self.precision("write_off_amount")):
            write_off_account_currency = get_account_currency(self.write_off_account)
            default_cost_center = frappe.get_cached_value('Company',  self.company,  'cost_center')

            gl_entries.append(
                self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": self.write_off_account,
                    "credit": flt(self.base_write_off_amount, self.precision("base_write_off_amount")),
                    "credit_in_account_currency": (flt(self.base_write_off_amount,
                        self.precision("base_write_off_amount")) if self.party_account_currency==self.company_currency
                        else flt(self.write_off_amount, self.precision("write_off_amount"))),
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center
                }, self.party_account_currency)
            )
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.write_off_account,
                    "against": self.customer,
                    "debit": flt(self.base_write_off_amount, self.precision("base_write_off_amount")),
                    "debit_in_account_currency": (flt(self.base_write_off_amount,
                        self.precision("base_write_off_amount")) if write_off_account_currency==self.company_currency
                        else flt(self.write_off_amount, self.precision("write_off_amount"))),
                    "cost_center": self.cost_center or self.write_off_cost_center or default_cost_center
                }, write_off_account_currency)
            )

    def make_gle_for_rounding_adjustment(self, gl_entries):
        if flt(self.rounding_adjustment, self.precision("rounding_adjustment")):
            round_off_account, round_off_cost_center = \
                get_round_off_account_and_cost_center(self.company)

            gl_entries.append(
                self.get_gl_dict({
                    "account": round_off_account,
                    "against": self.customer,
                    "credit_in_account_currency": flt(self.rounding_adjustment,
                        self.precision("rounding_adjustment")),
                    "credit": flt(self.base_rounding_adjustment,
                        self.precision("base_rounding_adjustment")),
                    "cost_center": self.cost_center or round_off_cost_center,
                }
            ))

    def update_billing_status_in_dn(self, update_modified=True):
        updated_delivery_notes = []
        for d in self.get("items"):
            if d.dn_detail:
                billed_amt = frappe.db.sql("""select sum(amount) from `tabAkonto Invoice Item`
                    where dn_detail=%s and docstatus=1""", d.dn_detail)
                billed_amt = billed_amt and billed_amt[0][0] or 0
                frappe.db.set_value("Delivery Note Item", d.dn_detail, "billed_amt", billed_amt, update_modified=update_modified)
                updated_delivery_notes.append(d.delivery_note)
            elif d.so_detail:
                updated_delivery_notes += update_billed_amount_based_on_so(d.so_detail, update_modified)

        for dn in set(updated_delivery_notes):
            frappe.get_doc("Delivery Note", dn).update_billing_percentage(update_modified=update_modified)

    def on_recurring(self, reference_doc, auto_repeat_doc):
        for fieldname in ("c_form_applicable", "c_form_no", "write_off_amount"):
            self.set(fieldname, reference_doc.get(fieldname))

        self.due_date = None

    def update_serial_no(self, in_cancel=False):
        """ update Akonto Invoice refrence in Serial No """
        invoice = None if (in_cancel or self.is_return) else self.name
        if in_cancel and self.is_return:
            invoice = self.return_against

        for item in self.items:
            if not item.serial_no:
                continue

            for serial_no in item.serial_no.split("\n"):
                if serial_no and frappe.db.exists('Serial No', serial_no):
                    sno = frappe.get_doc('Serial No', serial_no)
                    sno.sales_invoice = invoice
                    sno.db_update()

    def validate_serial_numbers(self):
        """
            validate serial number agains Delivery Note and Akonto Invoice
        """
        self.set_serial_no_against_delivery_note()
        self.validate_serial_against_delivery_note()
        self.validate_serial_against_sales_invoice()

    def set_serial_no_against_delivery_note(self):
        for item in self.items:
            if item.serial_no and item.delivery_note and \
                item.qty != len(get_serial_nos(item.serial_no)):
                item.serial_no = get_delivery_note_serial_no(item.item_code, item.qty, item.delivery_note)

    def validate_serial_against_delivery_note(self):
        """
            validate if the serial numbers in Akonto Invoice Items are same as in
            Delivery Note Item
        """

        for item in self.items:
            if not item.delivery_note or not item.dn_detail:
                continue

            serial_nos = frappe.db.get_value("Delivery Note Item", item.dn_detail, "serial_no") or ""
            dn_serial_nos = set(get_serial_nos(serial_nos))

            serial_nos = item.serial_no or ""
            si_serial_nos = set(get_serial_nos(serial_nos))

            if si_serial_nos - dn_serial_nos:
                frappe.throw(_("Serial Numbers in row {0} does not match with Delivery Note".format(item.idx)))

            if item.serial_no and cint(item.qty) != len(si_serial_nos):
                frappe.throw(_("Row {0}: {1} Serial numbers required for Item {2}. You have provided {3}.".format(
                    item.idx, item.qty, item.item_code, len(si_serial_nos))))

    def validate_serial_against_sales_invoice(self):
        """ check if serial number is already used in other Akonto Invoice """
        for item in self.items:
            if not item.serial_no:
                continue

            for serial_no in item.serial_no.split("\n"):
                sales_invoice = frappe.db.get_value("Serial No", serial_no, "sales_invoice")
                if sales_invoice and self.name != sales_invoice:
                    sales_invoice_company = frappe.db.get_value("Akonto Invoice", sales_invoice, "company")
                    if sales_invoice_company == self.company:
                        frappe.throw(_("Serial Number: {0} is already referenced in Akonto Invoice: {1}"
                            .format(serial_no, sales_invoice)))

    def update_project(self):
        if self.project:
            project = frappe.get_doc("Project", self.project)
            project.update_billed_amount()
            project.db_update()


    def verify_payment_amount_is_positive(self):
        for entry in self.payments:
            if entry.amount < 0:
                frappe.throw(_("Row #{0} (Payment Table): Amount must be positive").format(entry.idx))

    def verify_payment_amount_is_negative(self):
        for entry in self.payments:
            if entry.amount > 0:
                frappe.throw(_("Row #{0} (Payment Table): Amount must be negative").format(entry.idx))

    def get_discounting_status(self):
        status = None
        if self.is_discounted:
            invoice_discounting_list = frappe.db.sql("""
                select status
                from `tabInvoice Discounting` id, `tabDiscounted Invoice` d
                where
                    id.name = d.parent
                    and d.sales_invoice=%s
                    and id.docstatus=1
                    and status in ('Disbursed', 'Settled')
            """, self.name)
            for d in invoice_discounting_list:
                status = d[0]
                if status == "Disbursed":
                    break
        return status

    def set_status(self, update=False, status=None, update_modified=True):
        if self.is_new():
            if self.get('amended_from'):
                self.status = 'Draft'
            return

        if not status:
            if self.docstatus == 2:
                status = "Cancelled"
            elif self.docstatus == 1:
                self.status = "Submitted"
            else:
                self.status = "Draft"

        if update:
            self.db_set('status', self.status, update_modified = update_modified)

def validate_inter_company_party(doctype, party, company, inter_company_reference):
    if not party:
        return

    if doctype in ["Sales Invoice", "Akonto Invoice", "Sales Order"]:
        partytype, ref_partytype, internal = "Customer", "Supplier", "is_internal_customer"

        if doctype == "Akonto Invoice":
            ref_doc = "Purchase Invoice"
        else:
            ref_doc = "Purchase Order"
    else:
        partytype, ref_partytype, internal = "Supplier", "Customer", "is_internal_supplier"

        if doctype == "Purchase Invoice":
            ref_doc = "Akonto Invoice"
        else:
            ref_doc = "Sales Order"

    if inter_company_reference:
        doc = frappe.get_doc(ref_doc, inter_company_reference)
        ref_party = doc.supplier if doctype in ["Akonto Invoice", "Sales Order"] else doc.customer
        if not frappe.db.get_value(partytype, {"represents_company": doc.company}, "name") == party:
            frappe.throw(_("Invalid {0} for Inter Company Transaction.").format(partytype))
        if not frappe.get_cached_value(ref_partytype, ref_party, "represents_company") == company:
            frappe.throw(_("Invalid Company for Inter Company Transaction."))

    elif frappe.db.get_value(partytype, {"name": party, internal: 1}, "name") == party:
        companies = frappe.get_all("Allowed To Transact With", fields=["company"], filters={"parenttype": partytype, "parent": party})
        companies = [d.company for d in companies]
        if not company in companies:
            frappe.throw(_("{0} not allowed to transact with {1}. Please change the Company.").format(partytype, company))

def update_linked_doc(doctype, name, inter_company_reference):

    if doctype in ["Akonto Invoice", "Purchase Invoice"]:
        ref_field = "inter_company_invoice_reference"
    else:
        ref_field = "inter_company_order_reference"

    if inter_company_reference:
        frappe.db.set_value(doctype, inter_company_reference,\
            ref_field, name)

def unlink_inter_company_doc(doctype, name, inter_company_reference):

    if doctype in ["Akonto Invoice", "Purchase Invoice"]:
        ref_doc = "Purchase Invoice" if doctype == "Akonto Invoice" else "Akonto Invoice"
        ref_field = "inter_company_invoice_reference"
    else:
        ref_doc = "Purchase Order" if doctype == "Sales Order" else "Sales Order"
        ref_field = "inter_company_order_reference"

    if inter_company_reference:
        frappe.db.set_value(doctype, name, ref_field, "")
        frappe.db.set_value(ref_doc, inter_company_reference, ref_field, "")

def get_list_context(context=None):
    from erpnext.controllers.website_list_for_contact import get_list_context
    list_context = get_list_context(context)
    list_context.update({
        'show_sidebar': True,
        'show_search': True,
        'no_breadcrumbs': True,
        'title': _('Invoices'),
    })
    return list_context

@frappe.whitelist()
def get_bank_cash_account(mode_of_payment, company):
    account = frappe.db.get_value("Mode of Payment Account",
        {"parent": mode_of_payment, "company": company}, "default_account")
    if not account:
        frappe.throw(_("Please set default Cash or Bank account in Mode of Payment {0}")
            .format(mode_of_payment))
    return {
        "account": account
    }

@frappe.whitelist()
def make_maintenance_schedule(source_name, target_doc=None):
    doclist = get_mapped_doc("Akonto Invoice", source_name,     {
        "Akonto Invoice": {
            "doctype": "Maintenance Schedule",
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Akonto Invoice Item": {
            "doctype": "Maintenance Schedule Item",
        },
    }, target_doc)

    return doclist

@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = flt(source_doc.qty) - flt(source_doc.delivered_qty)
        target_doc.stock_qty = target_doc.qty * flt(source_doc.conversion_factor)

        target_doc.base_amount = target_doc.qty * flt(source_doc.base_rate)
        target_doc.amount = target_doc.qty * flt(source_doc.rate)

    doclist = get_mapped_doc("Akonto Invoice", source_name,     {
        "Akonto Invoice": {
            "doctype": "Delivery Note",
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Akonto Invoice Item": {
            "doctype": "Delivery Note Item",
            "field_map": {
                "name": "si_detail",
                "parent": "against_sales_invoice",
                "serial_no": "serial_no",
                "sales_order": "against_sales_order",
                "so_detail": "so_detail",
                "cost_center": "cost_center"
            },
            "postprocess": update_item,
            "condition": lambda doc: doc.delivered_by_supplier!=1
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "field_map": {
                "incentives": "incentives"
            },
            "add_if_empty": True
        }
    }, target_doc, set_missing_values)

    return doclist

@frappe.whitelist()
def make_sales_return(source_name, target_doc=None):
    from erpnext.controllers.sales_and_purchase_return import make_return_doc
    return make_return_doc("Akonto Invoice", source_name, target_doc)

def get_inter_company_details(doc, doctype):
    if doctype in ["Akonto Invoice", "Sales Order"]:
        party = frappe.db.get_value("Supplier", {"disabled": 0, "is_internal_supplier": 1, "represents_company": doc.company}, "name")
        company = frappe.get_cached_value("Customer", doc.customer, "represents_company")
    else:
        party = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 1, "represents_company": doc.company}, "name")
        company = frappe.get_cached_value("Supplier", doc.supplier, "represents_company")

    return {
        "party": party,
        "company": company
    }


def validate_inter_company_transaction(doc, doctype):

    details = get_inter_company_details(doc, doctype)
    price_list = doc.selling_price_list if doctype in ["Akonto Invoice", "Sales Order"] else doc.buying_price_list
    valid_price_list = frappe.db.get_value("Price List", {"name": price_list, "buying": 1, "selling": 1})
    if not valid_price_list:
        frappe.throw(_("Selected Price List should have buying and selling fields checked."))

    party = details.get("party")
    if not party:
        partytype = "Supplier" if doctype in ["Akonto Invoice", "Sales Order"] else "Customer"
        frappe.throw(_("No {0} found for Inter Company Transactions.").format(partytype))

    company = details.get("company")
    default_currency = frappe.get_cached_value('Company', company, "default_currency")
    if default_currency != doc.currency:
        frappe.throw(_("Company currencies of both the companies should match for Inter Company Transactions."))

    return

@frappe.whitelist()
def make_inter_company_purchase_invoice(source_name, target_doc=None):
    return make_inter_company_transaction("Akonto Invoice", source_name, target_doc)

def make_inter_company_transaction(doctype, source_name, target_doc=None):
    if doctype in ["Akonto Invoice", "Sales Order"]:
        source_doc = frappe.get_doc(doctype, source_name)
        target_doctype = "Purchase Invoice" if doctype == "Akonto Invoice" else "Purchase Order"
    else:
        source_doc = frappe.get_doc(doctype, source_name)
        target_doctype = "Akonto Invoice" if doctype == "Purchase Invoice" else "Sales Order"

    validate_inter_company_transaction(source_doc, doctype)
    details = get_inter_company_details(source_doc, doctype)

    def set_missing_values(source, target):
        target.run_method("set_missing_values")

    def update_details(source_doc, target_doc, source_parent):
        target_doc.inter_company_invoice_reference = source_doc.name
        if target_doc.doctype in ["Purchase Invoice", "Purchase Order"]:
            target_doc.company = details.get("company")
            target_doc.supplier = details.get("party")
            target_doc.buying_price_list = source_doc.selling_price_list
        else:
            target_doc.company = details.get("company")
            target_doc.customer = details.get("party")
            target_doc.selling_price_list = source_doc.buying_price_list

    doclist = get_mapped_doc(doctype, source_name,    {
        doctype: {
            "doctype": target_doctype,
            "postprocess": update_details,
            "field_no_map": [
                "taxes_and_charges"
            ]
        },
        doctype +" Item": {
            "doctype": target_doctype + " Item",
            "field_no_map": [
                "income_account",
                "expense_account",
                "cost_center",
                "warehouse"
            ]
        }

    }, target_doc, set_missing_values)

    return doclist

@frappe.whitelist()
def get_loyalty_programs(customer):
    ''' sets applicable loyalty program to the customer or returns a list of applicable programs '''
    from erpnext.selling.doctype.customer.customer import get_loyalty_programs

    customer = frappe.get_doc('Customer', customer)
    if customer.loyalty_program: return

    lp_details = get_loyalty_programs(customer)

    if len(lp_details) == 1:
        frappe.db.set(customer, 'loyalty_program', lp_details[0])
        return []
    else:
        return lp_details

@frappe.whitelist()
def create_invoice_discounting(source_name, target_doc=None):
    invoice = frappe.get_doc("Akonto Invoice", source_name)
    invoice_discounting = frappe.new_doc("Invoice Discounting")
    invoice_discounting.company = invoice.company
    invoice_discounting.append("invoices", {
        "sales_invoice": source_name,
        "customer": invoice.customer,
        "posting_date": invoice.posting_date,
        "outstanding_amount": invoice.outstanding_amount
    })

    return invoice_discounting
