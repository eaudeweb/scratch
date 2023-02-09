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

function toggleClick(x) {
  let value;
  if (x.hasClass('pressed')) {
    value = false;
    x.removeClass("pressed");
  }
  else {
    value = true;
    x.addClass("pressed");
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
  let is_detail_page = $('#tender_detail_table').length;
  let url = $(this).attr('data-url');

  if (button_id == 'fav_button') {
    let isFavorite = toggleClick($(this));
    let peopleIcon = $(this).closest("ul").find("i.people");
    let subTag = $(this).closest("ul").find("sub");
    $.ajax({
      ...ajaxParams,
      url: $(this).attr('data-url'),
      data: { favourite: isFavorite },
      dataType: null,
      success: function () {
        let totalFollowers = parseInt(subTag.html()) || 0;
        if (isFavorite){
          totalFollowers += 1;
          addFill(peopleIcon, "pressed");
          subTag.html(totalFollowers);
        } else {
          totalFollowers -= 1;
          if (!totalFollowers){
            removeFill(peopleIcon, "pressed")
            subTag.html('');
          }
        }
        console.log('Success');
      }
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
            let peopleIcon = $(`#add_follower_button_${tender_id}`);
            let starIcon = peopleIcon.closest("ul").find("i.fav_button");
            $.ajax({
              ...ajaxParams,
              contentType: "application/json; charset=utf-8",
              url: peopleIcon.attr('data-url'),
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
                let subTag = peopleIcon.siblings('sub');
                if (tender["old_followers"].has(loggedInUserId)){
                  addFill(starIcon, "pressed");
                } else {
                  removeFill(starIcon, "pressed");
                }
                if(totalFollowers){
                  subTag.html(totalFollowers);
                  addFill(peopleIcon, "pressed");
                } else {
                  subTag.html('');
                  removeFill(peopleIcon, "pressed");
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
    value = toggleClick($(this));
    $.ajax({
      ...ajaxParams,
      url: $(this).attr('data-url'),
      data: { seen: value },
    });
  }

  if (button_id == 'remove_button') {
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
      "orderable": false,
      "render": function (data, type, row) {

        return row['awards'].length > 0
        ? `<a class="award-link-icon" href=${row['awards']}><i class="bi bi-box-arrow-up-right"></i></a>`
        : '';
      }
    },
    {
      "targets": 5,  // Vendor(s)
      "orderable": false
    }
  ];

  const awardColumnDefs = [
    {
      "targets": 0,
      "orderable": true,
      "render": function (data, type, row) {
        return '<a href="' + row['url'] + '">' + data + '</a>';
      },
    },
    {
      "targets": 5,  // Published
      "orderable": false
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
    "order": [[5, "desc"]],  // Published
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
    "order": [[4, "desc"]],  // Award date
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
    $(this).DataTable(tableOptions[$(this).attr("id")]);
  })
}

function toggleHover(icon) {
  let classStr = icon.attr("class");
  icon.attr("class", classStr.replace(/bi-[a-z]+(-fill)?/g, function(m) {
    return m.endsWith("-fill") ? m.slice(0, -5) : m + "-fill";
  }));
}

function addFill(icon, classToAdd="") {
  let classStr = icon.attr("class");
  icon.attr("class", classStr.replace(/bi-(\w+) (.*)/g, 'bi-$1-fill $2'));
  icon.addClass(classToAdd);
}

function removeFill(icon, classToRemove="") {
  let classStr = icon.attr("class");
  icon.attr("class", classStr.replace("-fill", ""));
  icon.removeClass(classToRemove);
}

function activateHover() {
  $(".li_buttons").mouseenter(function () {
    let icon = $(this).find("i");
    toggleHover(icon);
  }).mouseleave(function () {
    let icon = $(this).find("i");
    if (icon.hasClass("pressed")){
      addFill(icon);
    } else {
      removeFill(icon);
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