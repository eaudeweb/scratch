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
      "pageLength": 50,
      lengthChange: false,

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
    let value;
    if ( $(this).hasClass('favourite_pressed')) {
      value = 'true';
    }
    else {
      value = 'false';
    }
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

  });

})


function myFunction(x) {
  if (x.classList.contains('favourite_pressed')) {
    x.classList.remove('favourite_pressed');
    x.classList.add('favourite_button');
  }
  else {
    x.classList.add("favourite_pressed");
  }
}



