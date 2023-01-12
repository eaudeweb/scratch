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

function toggleFavourite(x) {
  let value;
  if (x.hasClass('pressed')) {
    value = false;
    x.addClass("fa-regular").removeClass("fa-solid").removeClass("pressed");
  }
  else {
    x.addClass("fa-solid").addClass("pressed").removeClass("fa-regular");
    value = true;
  }

  return value;
}

function toggleSeen(x) {
  let value;
  let usr = document.getElementById("seen_usr");

  if (x.hasClass('pressed')) {
    value = false;
    usr.textContent = '';
    x.addClass("fa-regular").removeClass("fa-solid").removeClass("pressed");
  }
  else {
    x.addClass("fa-solid").addClass("pressed").removeClass("fa-regular");
    try {
      usr.textContent = document.getElementById("usr_seen_by").textContent;
    }
    catch (err) {

    }
    value = true;
  }

  return value;
}

function buttonsClick() {

  let button_id = $(this).attr('id');
  let is_detail_page = (button_id == 'remove_button_detail');

  if (button_id == 'fav_button') {
    let value = toggleFavourite($(this));
    $.ajax({
      type: "POST",
      url: $(this).attr('data-url'),
      data: { favourite: value },
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
      url: $(this).attr('data-url'),
      data: { seen: value },
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
    let url = $(this).attr('data-url');
    $.confirm({
      title: 'Are you sure you want to delete this tender?',
      content: $(this).attr('data-name').toString(),
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
              if (is_detail_page) {
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
}

const tableColumns = {
  "tender_table": [
    { "data": "title" },
    { "data": "source" },
    { "data": "organization" },
    { "data": "deadline" },
    { "data": "published" },
    { "data": "notice_type" }
  ],
  "archive_table": [
    { "data": "title" },
    { "data": "source" },
    { "data": "organization" },
    { "data": "deadline" },
    { "data": "published" },
    { "data": "notice_type" }
  ],
  "contract_awards_table": [
    { "data": "title" },
    { "data": "source" },
    { "data": "organization" },
    { "data": "award_date" },
    { "data": "renewal_date" },
    { "data": "vendor" },
    { "data": "value" },
    { "data": "currency" }
  ],
};

function tenderData(d) {
  d.organization = $('#id_organization').val();
  d.status = $('#id_status').val();
  d.source = $('#id_source').val();
  d.favourite = $('#id_favourite').val();
  d.has_keywords = $('#id_keyword').val();
  d.notice_type = $('#id_type').val();
  d.seen = $('#id_seen').val();
  d.tags = $('#id_tags').val().join(',');
  d.ungm_deadline_today = ungm_deadline_today;
  d.ted_published_today = ted_published_today;
  d.ted_deadline_today = ted_deadline_today;
  d.ungm_published_today = ungm_published_today;
}

function awardData(d) {
  d.organization = $('#id_organization').val();
  d.source = $('#id_source').val();
  d.vendor = $('#id_vendor').val();
  d.value = $('#id_value').val();
}

function initDataTables() {
  $.fn.dataTable.moment('DD MMM YYYY');
  $.fn.dataTable.moment('DD MMM YYYY, HH:mm');

  let doc = this;

  const searchTerm = $.urlParam(doc, 'terms');
  const ungm_deadline_today = $.urlParam(doc, 'ungm_deadline_today');
  const ted_published_today = $.urlParam(doc, 'ted_published_today');
  const ted_deadline_today = $.urlParam(doc, 'ted_deadline_today');
  const ungm_published_today = $.urlParam(doc, 'ungm_published_today');

  const tenderOptions = {
    "columnDefs": [
      { "width": "55%", "targets": 0 },
      { "width": "10%", "targets": 3 },
      { "width": "8%", "targets": 4 },
      { "width": "8%", "targets": 5 },
    ],
    "order": [[4, "desc"]],
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
        d.tags = $('#id_tags').val().join(',');
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
        "render": function (data, type, row) {
          return '<a href="' + row['url'] + '">' + data + '</a>';
        }
      },
    ],
    "columns": [
      { "data": "title" },
      { "data": "source" },
      { "data": "organization" },
      { "data": "deadline" },
      { "data": "published" },
      { "data": "tags" },
      { "data": "notice_type" }
    ],
    "drawCallback": function (settings) {
      $("i").click(buttonsClick);
      activateHover();
    }
  };

  const archiveOptions = {
    ...tenderOptions,
    "ajax": {
      ...tenderOptions.ajax,
      "url": "/archive/ajax"
    }
  };

  const awardOptions = {
    ...tenderOptions,
    "ajax": {
      "url": "/awards/ajax",
      "type": "GET",
      "data": function (d) {
        d.organization = $('#id_organization').val();
        d.source = $('#id_source').val();
        d.vendor = $('#id_vendor').val();
        d.value = $('#id_value').val();
      }
    },
    "columns": [
      { "data": "title" },
      { "data": "source" },
      { "data": "organization" },
      { "data": "award_date" },
      { "data": "renewal_date" },
      { "data": "vendor" },
      { "data": "value" },
      { "data": "currency" }
    ]
  };

  const tableOptions = {
    "tenders_table": tenderOptions,
    "archive_table": archiveOptions,
    "contract_awards_table": awardOptions,
    "tender_detail_table": {
      "searching": false,
      "bPaginate": false,
      "bLengthChange": false,
      "bInfo": false,
      "ordering": false,
      "drawCallback": function (settings) {
        $('i').click(buttonsClick);
        activateHover();
      }
    }
  }

  let table = $(".table table, .table_detail table");
  return table.DataTable(tableOptions[table.attr("id")]);
}

function activateHover() {
  $(".li_buttons").mouseenter(function () {
    let icon = $(this).find("i");
    if (icon.hasClass("pressed")) {
      icon.addClass("fa-regular").removeClass("fa-solid");
    } else {
      icon.addClass("fa-solid").removeClass("fa-regular");
    }
  }).mouseleave(function () {
    let icon = $(this).find("i");
    if (icon.hasClass("pressed")) {
      icon.addClass("fa-solid").removeClass("fa-regular");
    } else {
      icon.addClass("fa-regular").removeClass("fa-solid");
    }
  });
}

$(document).ready(function () {
  $('#id_vendor').select2();
  $('#id_organization').select2();
  $('#id_tags').select2();

  initDataTables();
});