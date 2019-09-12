$(document).ready(function () {
  let scroll_size = $('#log_container').height() * 0.8;
  $('#log_table').DataTable({
    "order": [[ 0, "desc" ]],
    "lengthChange": false,
    "searching": false,
    "pageLength": 6,
    "bInfo": false,
    "columnDefs": [
      { "orderable": false, "targets": 0 }
    ],
    "dom": 't<"bottom"flp><"clear">',
    "bScrollCollapse" : false,
    "sScrollY": scroll_size,
  });
});
