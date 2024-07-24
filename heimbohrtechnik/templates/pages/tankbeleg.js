$('document').ready(function(){
    make();
    run();
});


function make() {
    // attach button handlers
    $(".btn-submit").on('click', function() { 
        // validate input
        if ((!document.getElementById('truck').value)
            || (!document.getElementById('key').value)) {
            frappe.msgprint( __("Ungültige Parameter, bitte Seite neu laden.") );
        } else if ((!document.getElementById('amount').value)
            || (!document.getElementById('currency').value)) {
            document.getElementById('amount').focus();
            frappe.msgprint( __("Bitte einen Betrag eingeben.") );
        } else if (!document.getElementById('payment').value) {
            document.getElementById('amount').focus();
            frappe.msgprint( __("Bitte eine Zahlugnsweise eingeben.") );
        } else if (!document.getElementById('kilometer').value) {
            document.getElementById('kilometer').focus();
            frappe.msgprint( __("Bitte den Kilometerstand eingeben.") );
        } else if (!document.getElementById('liter').value) {
            document.getElementById('liter').focus();
            frappe.msgprint( __("Bitte die Anzahl Liter eingeben.") );
        } else if (!document.getElementById('image-input').value) {
            document.getElementById('image-input').focus();
            frappe.msgprint( __("Bitte den Beleg anhängen.") );
        } else {
            frappe.call({
                'method': 'heimbohrtechnik.templates.pages.tankbeleg.insert_receipt',
                'args': {
                    'truck': document.getElementById('truck').value, 
                    'key': document.getElementById('key').value, 
                    'date': formatDate(new Date()), 
                    'amount': document.getElementById('amount').value, 
                    'payment': document.getElementById('payment').value, 
                    'currency': document.getElementById('currency').value,
                    'kilometer': document.getElementById('kilometer').value, 
                    'liter': document.getElementById('liter').value,
                    'operating_hours': document.getElementById('operating_hours').value
                },
                'callback': function(r) {
                    if (typeof r.message !== 'undefined') {
                        var txt_success = document.getElementById('result-doc');
                        txt_success.innerHTML = "<p>" + r.message + "</p>";
                        // upload picture
                        uploadPicture(r.message);
                    } else {
                        console.log("Invalid response");
                    }
                }
            });
        }
    });
}

function run() {
    // get command line parameters
    var arguments = window.location.toString().split("?");
    if (!arguments[arguments.length - 1].startsWith("http")) {
        var args_raw = arguments[arguments.length - 1].split("&");
        var args = {};
        args_raw.forEach(function (arg) {
            var kv = arg.split("=");
            if (kv.length > 1) {
                args[kv[0]] = kv[1];
            }
        });
        if (args['truck']) {
            document.getElementById('truck').value = args['truck'];
        }
        if (args['key']) {
            document.getElementById('key').value = args['key'];
        }        
    } else {
        // no arguments provided
        
    }
}

function uploadPicture(receipt) {
    var fileInput = document.getElementById("image-input");
    var file = fileInput.files[0];

    if (file) {
        var fileType = file.type;
        if (fileType === "image/jpeg" || fileType === "image/png") {
            var reader = new FileReader();
            reader.onload = function(e) {
                var fileData = e.target.result;
                frappe.call({
                    'method': "heimbohrtechnik.templates.pages.tankbeleg.upload_picture",
                    'args': {
                        'truck': document.getElementById('truck').value, 
                        'key': document.getElementById('key').value, 
                        'receipt': receipt, 
                        'picture_data': fileData
                    },
                    'callback': function(r) {
                        var btn_submit = document.getElementById('submit');
                        btn_submit.disabled = true;
                        btn_submit.style.visibility = "hidden";
                        var row_success = document.getElementById('finalised-row');
                        row_success.style.visibility = "visible";
                        document.getElementById('load_type').disabled = true;
                    }
                });
            };
            reader.readAsDataURL(file);
        } else {
            alert("Bitte wählen Sie ein Bild im Format JPEG oder PNG aus.");
            return;
        }
    }
}

function formatDate(date) {
    var d = new Date(date);
    var month = '' + (d.getMonth() + 1);
    var day = '' + d.getDate();
    var year = d.getFullYear();

    if (month.length < 2) month = '0' + month;
    if (day.length < 2) day = '0' + day;

    return [year, month, day].join('-');
}
