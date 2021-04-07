# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

# searches for supplier
def supplier_by_capability(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabSupplier`.`name`, `tabSupplier`.`supplier_name`
           FROM `tabSupplier`
           LEFT JOIN `tabSupplier Activity` ON `tabSupplier Activity`.`parent` = `tabSupplier`.`name`
           WHERE `tabSupplier Activity`.`activity` = "{c}";
        """.format(c=filters['capability']))
