$(document).ready(function() {
    $('#tenders_table').DataTable(
        {
            "order": [[ 3, "desc" ]],
            "pageLength": 50,
            lengthChange: false,

        });

})