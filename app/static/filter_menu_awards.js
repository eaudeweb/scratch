$(document).ready(function() {
  enableFilterButton();
  $('#form_id').click(function() {
    enableFilterButton();
  });

})

function enableFilterButton() {
  let organisation = $('#id_organization').val();
  let vendor = $('#id_vendor').val();
  let source = $('#id_source').val();
  let value = $('#id_value').val();

  if (organisation || source || vendor || value)
    $("button[name='filter_button']").prop("disabled", false);
}
