$('document').ready(function(){
    make();
    run();
});


function make() {
}
function run() {
    $(".btn-submit").on('click', function() { 
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.schlammanlieferung.insert_delivery',
            'args': {
                'drilling_team': document.getElementById('drilling_team').value, 
                'drilling_meter': document.getElementById('drilling_meter').value, 
                'date': document.getElementById('date').value, 
                'project': document.getElementById('project').value, 
                'project2': document.getElementById('project2').value
            },
            'callback': function(r) {
                console.log("Du Maschine!");
            }
        });
    });
}
