$(document).ready(function() {
  enableFilterButton();
  $('#form_id').click(function() {
    enableFilterButton();
  });

})

function enableFilterButton() {
  let organisation = $('#id_organization').val();
  let status = $('#id_status').val();
  let source = $('#id_source').val();
  let favourite = $('#id_favourite').val();

  if (organisation || status || source || favourite)
    $("button[name='filter_button']").prop("disabled", false);
}
