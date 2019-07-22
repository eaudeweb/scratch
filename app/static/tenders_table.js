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

$(window).add(function() {
  let url = $('#fav_button').attr('action');
  console.log($('#fav_button').attr('action'));
  $.ajax({
    type: "GET",
    url: url,
    data: {},
    beforeSend: function (xhr) {
      xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    },
    success: function (response) {

      if(response['favourite'] == true) {
        $('#fav_button').addClass('favourite_pressed');
        console.log($('#fav_button').hasClass('favourite_pressed'));
      }
      console.log(response['favourite'])
    },
    fail: function(xhr, textStatus, errorThrown) {
      alert('request failed');
      console.log(errorThrown);
    },
    dataType: 'json',
  });


});

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

  $('#fav_button').click(function () {
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
  let button = document.getElementById("fav_button");

  if (button.classList.contains('favourite_pressed'))
    button.classList.remove('favourite_pressed')
  else
    button.classList.add("favourite_pressed");
}



