class IntegerSet extends Set {
  constructor(iterable) {
    if (iterable) {
      iterable = [...iterable].map(val => {
        return parseInt(val);
      });
    }
    super(iterable);
  }

  add(value) {
    super.add(parseInt(value));
  }

  addSet(setToAdd) {
    setToAdd.forEach(elem => this.add(elem));
  }

  deleteSet(setToDelete) {
    setToDelete.forEach(elem => this.delete(elem));
  }

  has(value) {
    return super.has(parseInt(value));
  }

}

var tenderFollowers = {};

function copyFollowers(followers) {
  let copy = {};
  for(let key in followers) {
    copy[key] = new IntegerSet([...followers[key]]);
  }
  return copy;
}

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

let ajaxParams = {
    type: "POST",
    success: function () {
      console.log('Success');
    },
    beforeSend: function (xhr) {
      xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    },
    dataType: 'json',
  };

function populateUserList(tender_id) {
  let url = $(`#add_follower_button_${tender_id}`).attr("data-url");
  $(`#user_table_for_tender_${tender_id}`).DataTable({
    paging: false,
    ordering: false,
    info: false,
    language: {
      search: '',
    },
    ajax: {
      url: url,
      dataSrc: ''
    },
    columns: [
      {
        data: function(row, type, set, meta){
          if(!(tender_id in tenderFollowers)){
            tenderFollowers[tender_id] = {
              old_followers: new IntegerSet(),
              new_followers: new IntegerSet(),
              unfollowers: new IntegerSet(),
            };
          }
          let checked = '';
          if(row["is_follower"]){
            checked = ' checked';
            tenderFollowers[tender_id]["old_followers"].add(row["id"]);
          }
          let email = row["email"] || 'no email';
          return `
          <label>
            <input type="checkbox" name="${row["username"]}" class="user_checkbox" data-tender-id="${tender_id}" data-user-id="${row["id"]}" ${checked}>
            ${row["username"]}<span class="user_email"> &lt;${email}&gt;</span>
          </label>
          `;
        }
      }
    ],
    drawCallback: function(){
      $(".user_checkbox").change(function(){
        let tenderId = $(this).attr("data-tender-id");
        let userId = $(this).attr("data-user-id");
        if(this.checked){
          if(!tenderFollowers[tenderId]["old_followers"].has(userId)){
            tenderFollowers[tenderId]["new_followers"].add(userId);
          } else {
            tenderFollowers[tenderId]["unfollowers"].delete(userId);
          }
        } else {
          if(tenderFollowers[tenderId]["old_followers"].has(userId)){
            tenderFollowers[tenderId]["unfollowers"].add(userId);
          } else {
            tenderFollowers[tenderId]["new_followers"].delete(userId);
          }
        }
        let somethingChanged = (
          tenderFollowers[tenderId]["new_followers"].size
          || tenderFollowers[tenderId]["unfollowers"].size
        )

        if(somethingChanged){
          $(`.save_tender_${tenderId}_followers`).prop("disabled", false);
        } else {
          $(`.save_tender_${tenderId}_followers`).prop("disabled", true);
        }
      });
    }
  });
  $(".jconfirm-content-pane").css("max-height", "none");
}

function toJSON(object){
  // Replace sets with arrays to allow proper JSON conversion
  let newObject = {...object};
  for(const key in newObject){
    newObject[key] = [...object[key]]
  }
  return JSON.stringify(newObject);
}

function buttonsClick() {

  let button_id = $(this).attr('id');
  let tender_id = $(this).closest("tr").attr("id");
  let is_detail_page = (button_id == 'remove_button_detail');

  if (button_id == 'fav_button') {
    let value = toggleFavourite($(this));
    $.ajax({
      ...ajaxParams,
      url: $(this).attr('data-url'),
      data: { favourite: value },
    });
  }

  if (button_id.startsWith('add_follower_button')) {
    $.confirm({
      title: 'Manage tender followers',
      content: `
      <table id="user_table_for_tender_${tender_id}" class="table table-striped table-hover">
      <thead>
        <tr>
          <th>Users</th>
        </tr>
      </thead>
      </table>
      `,
      type: 'dark',
      closeIcon: true,
      theme: 'material',
      buttons: {
        SAVE: {
          btnClass: `save_tender_${tender_id}_followers`,
          isDisabled: true,
          action: function () {
            let payload = toJSON(tenderFollowers[tender_id]);
            let iconBtn = $(`#add_follower_button_${tender_id}`);
            $.ajax({
              ...ajaxParams,
              contentType: "application/json; charset=utf-8",
              url: iconBtn.attr('data-url'),
              data: payload,
              success: function (result) {
                let tender = tenderFollowers[tender_id];
                tender["old_followers"].addSet(tender["new_followers"]);
                tender["old_followers"].deleteSet(tender["unfollowers"]);
                tender["new_followers"] = new IntegerSet();
                tender["unfollowers"] = new IntegerSet();
                let totalFollowers = (
                  tenderFollowers[tender_id]["old_followers"].size
                  + tenderFollowers[tender_id]["new_followers"].size
                  - tenderFollowers[tender_id]["unfollowers"].size
                );
                if(totalFollowers){
                  iconBtn.siblings('sub').html(totalFollowers);
                  iconBtn.addClass('pressed fa-solid').removeClass('fa-regular');
                } else {
                  iconBtn.siblings('sub').html('');
                  iconBtn.addClass('fa-regular').removeClass('pressed fa-solid');
                }
                console.log('Success');
              },
              dataType: 'text',
            });
          }
        },
      },
      onContentReady: function(){
        populateUserList(tender_id);
      }
    });
  }

  if (button_id == 'seen_button') {
    let value;
    value = toggleSeen($(this));
    $.ajax({
      ...ajaxParams,
      url: $(this).attr('data-url'),
      data: { seen: value },
    });
  }

  if (button_id == 'remove_button_list' || button_id == 'remove_button_detail') {
    $.confirm({
      title: 'Are you sure you want to delete this tender?',
      content: $(this).attr('data-name').toString(),
      type: 'dark',
      closeIcon: true,
      theme: 'material',
      buttons: {
        YES: function () {
          $.ajax({
            ...ajaxParams,
            url: $(this).attr('data-url'),
            data: {},
            success: function (result) {
              if (is_detail_page) {
                window.location = result
              }
              else {
                location.reload();
              }
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
    { "data": "notice_type" },
    { "data": "awards"}
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

  const tendersColumnDefs = [
    {
      "targets": 0,
      "orderable": true,
      "render": function (data, type, row) {
        return '<a href="' + row['url'] + '">' + data + '</a>';
      },
    },
    {
      "targets": 1,
      "orderable": true,
      "render": function (data, type, row) {

        return row['awards'].length > 0
        ? `<a class="award-link-icon" href=${row['awards']}><i class="fa fa-external-link fa-lg" ></i> </a>`
        : '';
      }
    }
  ];

  const awardColumnDefs = [
    {
      "targets": 0,
      "orderable": true,
      "render": function (data, type, row) {
        return '<a href="' + row['url'] + '">' + data + '</a>';
      },
    }
  ]

  const tenderOptions = {
    "rowId": "id",
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
    "language": {
      "search": '',
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
    columnDefs: tendersColumnDefs,
    "columns": [
      { "data": "title" },
      { "data": "awards"},
      { "data": "source" },
      { "data": "organization" },
      { "data": "deadline" },
      { "data": "published" },
      { "data": "tags" },
      { "data": "notice_type" },
    ],
    "drawCallback": function (settings) {
      $("i").click(buttonsClick);
      activateHover();
    }
  };

  const archiveOptions = {
    ...tenderOptions,
    "columnDefs": tendersColumnDefs,
    "ajax": {
      ...tenderOptions.ajax,
      "url": "/archive/ajax"
    }
  };

  const awardOptions = {
    ...tenderOptions,
    "columnDefs": awardColumnDefs,
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

  const vendorOptions = {
    "order": [[ 0, "asc" ]],
    "pageLength": 50,
    "lengthChange": false,
    "search": {
      "search": searchTerm
    },
    "language": {
      "search": '',
    },
    "processing": true,
    "serverSide": true,
    "ajax": {
      "url": "/vendors/ajax",
      "type": "GET",
      "data": function (d) {
      }
    },
    columnDefs: [
    {
      "targets": 0,
      "orderable": true,
      "render": function ( data, type, row ) {
          return '<a href="' + row['url'] +'">' + data + '</a>';
       },
    }
    ],
    "columns": [
      { "data": "name" },
      { "data": "email" },
      { "data": "contact_name" },
    ],
    "drawCallback": function(settings) {
        $('button').click(buttonsClick)
    }
  };

  const tableOptions = {
    "tenders_table": tenderOptions,
    "tenders_table_archive": archiveOptions,
    "contract_awards_table": awardOptions,
    "vendors_table": vendorOptions,
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

  const tableIds = `#tenders_table, #tenders_table_archive,
  #contract_awards_table, #vendors_table, #tender_detail_table`;

  $(tableIds).each(function(){
    $(this).DataTable(tableOptions[$(this).attr("id")])
  })
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

  $('#tenders_table').on('draw.dt', function () {
    $("#tenders_table td a.award-link-icon").closest("tr").css("background-color", "#eaff7b");
  });

});