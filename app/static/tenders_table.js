function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie != '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) == (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

$(document).ready(function() {
  $('#tenders_table').DataTable(
    {
      "order": [[ 3, "desc" ]],
      "pageLength": 15,
      lengthChange: false,
      "scrollY":  "625px",
      "scrollCollapse": true,

    });

  $('#tender_detail_table').DataTable(
    {
      "searching": false,
      "bPaginate": false,
      "bLengthChange": false,
      "bInfo" : false,
      "ordering": false,
    });

  $('button').click(function () {

    if ($(this).attr('id') == 'fav_button') {
      let value;
      value = toggleFavourite($(this));
      $.ajax({
        type: "POST",
        url: $(this).attr('action'),
        data: {favourite: value},
        success: function () {
          console.log('Success');
        },
        beforeSend: function (xhr) {
          xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        },
        dataType: 'json',
      });
    }
  });

})


function toggleFavourite(x) {
  let value;
  if (x.hasClass('favourite_pressed')) {
    value = false;
    x.removeClass('favourite_pressed');
    x.addClass('favourite_button');
  }
  else {
    x.addClass("favourite_pressed");
    value = true;
  }

  return value;
}

