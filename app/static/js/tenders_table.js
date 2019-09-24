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

$.urlParam = function (doc, name) {
    const results = new RegExp('[\?&]' + name + '=([^&#]*)')
                      .exec(doc.location.search);
    return (results !== null) ? decodeURIComponent(results[1]) : '';
};

$(document).ready(function() {
  $.fn.dataTable.moment( 'DD MMM YYYY');
  $.fn.dataTable.moment( 'DD MMM YYYY, HH:mm');

  let doc = this;

  const searchTerm = $.urlParam(doc, 'terms');

  $('#tenders_table').DataTable(
    {
      "columnDefs": [
        { "width": "55%", "targets": 0 },
        { "width": "10%", "targets": 3 },
        { "width": "8%", "targets": 4 },
        { "width": "8%", "targets": 5 },
      ],
      "order": [[ 4, "desc" ]],
      "pageLength": 10,
      "lengthChange": false,
      "search": {
        "search": searchTerm
      }
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

    let button_id = $(this).attr('id');
    let page = (button_id == 'remove_button_detail') ? 1 : 2;

    if (button_id == 'fav_button') {
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

    if (button_id == 'seen_button') {
      let value;
      value = toggleSeen($(this));
      $.ajax({
        type: "POST",
        url: $(this).attr('action'),
        data: {seen: value},
        success: function () {
          console.log('Success');
        },
        beforeSend: function (xhr) {
          xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        },
        dataType: 'json',
      });
    }

    if (button_id == 'remove_button_list' || button_id == 'remove_button_detail') {
      let url = $(this).attr('action');
      $.confirm({
        title: 'Are you sure you want to delete this tender?',
        content: $(this).attr('name').toString(),
        type: 'dark',
        closeIcon: true,
        theme: 'material',
        buttons: {
          YES: function () {
            $.ajax({
              type: "POST",
              url: url,
              data: {},
              success: function (result) {
                console.log(page);
                if (page == 1) {
                  window.location = result
                }
                else {
                  location.reload();
                }
              },
              beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
              },
              dataType: 'text',
            });
          }
        }
      });
    }
  });
});

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

function toggleSeen(x) {
  let value;
  let usr = document.getElementById("seen_usr");

  if (x.hasClass('seen_pressed')) {
    value = false;
    usr.textContent = '';
    x.removeClass('seen_pressed');
    x.addClass('seen_button');
  }
  else {
    x.addClass("seen_pressed");
    usr.textContent = document.getElementById("usr_seen_by").textContent;
    value = true;
  }

  return value;
}
