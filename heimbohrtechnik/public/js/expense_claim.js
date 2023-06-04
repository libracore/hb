frappe.ui.form.on('Expense Claim', {
    before_save(frm) {
        // check that all payments except cash are not paid to employee
        for (var i = 0; i < frm.doc.expenses.length; i++) {
            if (frm.doc.expenses[i].payment !== "Bar") {
                frm.doc.expenses[i].sanctioned_amount = 0;
            }
        }
    }
});
