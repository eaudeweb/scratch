function sentenceCase(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

$(document).ready(function () {
  let tableOptions = {
    searching: false,
    pagination: true,
    pageLength: 10,
    lengthChange: false,
    ordering: false,
    processing: true,
    serverSide: true,
    ajax: "/tasks/ajax",
    columns: [
      { "data": "args"},
      { "data": "kwargs" },
      { "data": "started" },
      { "data": "stopped" },
      { "data": "output" },
      { "data": "status" },
      {
        "data": null,
        "render": function (data, type, row, meta) {
          return `
            <a href="" class="rm-link" title="Delete log entry" data-bs-toggle="modal" data-bs-target="#rm-${row.id}">
              <i class="bi bi-trash"></i>
            </a>
            <div id="rm-${row.id}" class="modal" tabindex="-1">
              <div class="modal-dialog modal-dialog-scrollable">
                <div class="modal-content">
                  <div class="modal-header">
                    <h5 class="modal-title">Are you sure you want to delete this log entry?</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <a href="/management/delete/${row.id}">
                      <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Delete</button>
                    </a>
                  </div>
                </div>
              </div>
            </div>`;
        }
      }
    ],
    columnDefs: [
      {
        "targets": 4,
        "render": function (data, type, row) {
            let output = data ? data : "";
            if (output.length > 255) {
              return `${output.slice(0, 255)}...
              <a href="" data-bs-toggle="modal" data-bs-target="#${row.id}">
                See more
              </a>
              <div id="${row.id}" class="modal" tabindex="-1">
                <div class="modal-dialog modal-dialog-scrollable">
                  <div class="modal-content">
                    <div class="modal-header">
                      <h5 class="modal-title">Output report</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                      ${data}
                    </div>
                    <div class="modal-footer">
                      <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Close</button>
                    </div>
                  </div>
                </div>
              </div>
              `;
            }
            return output;
        },
      },
      {
        "targets": 5,
        "render": function (data, type, row) {
          return  `<img src="../static/images/${row.status}.png" class="icon-log" title="${sentenceCase(row.status)}"></img>`;
        }
      }
    ],
    drawCallback: function (settings) {
      $('#task-table tr').hover(
        function() {
          $(this).find('a').css('visibility', 'visible');
        },
        function() {
          $(this).find('a').css('visibility', 'hidden');
        }
      );
    }
  };
  $('#task-table').DataTable(tableOptions);
});