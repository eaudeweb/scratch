$(document).ready(function() {
  $('#tenders_table').DataTable(
    {
      "order": [[ 3, "desc" ]],
      "pageLength": 50,
      lengthChange: false,

    });
})


$(document).ready(function() {
    $('#tender_detail_table').DataTable(
        {
            "searching": false,
            "bPaginate": false,
            "bLengthChange": false,
            "bInfo" : false,
            "ordering": false,
        });

})

