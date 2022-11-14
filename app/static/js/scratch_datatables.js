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
  const ungm_deadline_today = $.urlParam(doc, 'ungm_deadline_today');
  const ted_published_today = $.urlParam(doc, 'ted_published_today');
  const ted_deadline_today = $.urlParam(doc, 'ted_deadline_today');
  const ungm_published_today = $.urlParam(doc, 'ungm_published_today');
  const archive = $.urlParam(doc, 'archive');

  $('#id_organization').select2();
  $('#id_vendor').select2();

  function buttonsClick() {

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
  };

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
      },
      "processing": true,
      "serverSide": true,
      "ajax": {
        "url": "/tenders/ajax",
        "type": "GET",
        "data": function (d) {
          d.organization = $('#id_organization').val();
          d.status = $('#id_status').val();
          d.source = $('#id_source').val();
          d.favourite = $('#id_favourite').val();
          d.has_keywords = $('#id_keyword').val();
          d.notice_type = $('#id_type').val();
          d.seen = $('#id_seen').val();
          d.ungm_deadline_today = ungm_deadline_today;
          d.ted_published_today = ted_published_today;
          d.ted_deadline_today = ted_deadline_today;
          d.ungm_published_today = ungm_published_today;
        },
      },
      columnDefs: [
      {
       "targets": 0,
       "orderable": true,
        "render": function ( data, type, row ) {
            return '<a href="' + row['url'] +'">' + data + '</a>';
        }
     },
     ],
      "columns": [
        { "data": "title" },
        { "data": "source" },
        { "data": "organization" },
        { "data": "deadline" },
        { "data": "published" },
        { "data": "notice_type" }
    ],
      "drawCallback": function(settings) {
          $('button').click(buttonsClick)
      }
    });

    $('#tenders_table_archive').DataTable(
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
        },
        "processing": true,
        "serverSide": true,
        "ajax": {
          "url": "/archive/ajax",
          "type": "GET",
          "data": function (d) {
            d.organization = $('#id_organization').val();
            d.status = $('#id_status').val();
            d.source = $('#id_source').val();
            d.favourite = $('#id_favourite').val();
            d.has_keywords = $('#id_keyword').val();
            d.notice_type = $('#id_type').val();
            d.seen = $('#id_seen').val();
            d.ungm_deadline_today = ungm_deadline_today;
            d.ted_published_today = ted_published_today;
            d.ted_deadline_today = ted_deadline_today;
            d.ungm_published_today = ungm_published_today;
          },
        },
        columnDefs: [
        {
         "targets": 0,
         "orderable": true,
          "render": function ( data, type, row ) {
              return '<a href="' + row['url'] +'">' + data + '</a>';
          }
       },
       ],
        "columns": [
          { "data": "title" },
          { "data": "source" },
          { "data": "organization" },
          { "data": "deadline" },
          { "data": "published" },
          { "data": "notice_type" }
      ],
        "drawCallback": function(settings) {
            $('button').click(buttonsClick)
        }
      });

  $('#contract_awards_table').DataTable(
    {
      "order": [[ 3, "desc" ]],
      "pageLength": 10,
      "lengthChange": false,
      "search": {
        "search": searchTerm
      },
      "processing": true,
      "serverSide": true,
      "ajax": {
        "url": "/awards/ajax",
        "type": "GET",
        "data": function (d) {
          d.organization = $('#id_organization').val();
          d.source = $('#id_source').val();
          d.vendor = $('#id_vendor').val();
          d.value = $('#id_value').val();
        },
      },
      columnDefs: [
      {
        "targets": 0,
        "orderable": true,
        "render": function ( data, type, row ) {
            return '<a href="' + row['url'] +'">' + data + '</a>';

        },
      },
      {
        "targets": 4,
        "orderable": false,
      },
      ],
      "columns": [
        { "data": "title" },
        { "data": "source" },
        { "data": "organization" },
        { "data": "award_date" },
        { "data": "vendor" },
        { "data": "value" },
        { "data": "currency" }
    ],
      "drawCallback": function(settings) {
          $('button').click(buttonsClick)
      }
    });

  $('#tender_detail_table').DataTable(
    {
      "searching": false,
      "bPaginate": false,
      "bLengthChange": false,
      "bInfo" : false,
      "ordering": false,
      "drawCallback": function(settings) {
          $('button').click(buttonsClick)
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
    try {
      usr.textContent = document.getElementById("usr_seen_by").textContent;
    }
    catch(err){

    }
      value = true;
  }

  return value;
}
