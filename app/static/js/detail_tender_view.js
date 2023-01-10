
function pushNewTagToTable(tagInputValue) {
    tagInputValue = tagInputValue.trim()

    const tagsList = $("#tags_list_displayed")
    const tagsListValues = tagsList.text().split(',')

    const trimmedArray = tagsListValues.map(str => str.replace('\n','').trim());
    if (!trimmedArray.includes(tagInputValue)) {
        tagsListValues.push(tagInputValue)

        const filteredArr = tagsListValues.filter(function (element) {
            return element.trim() !== '';
        });

        tagsList.html(filteredArr.join(', '))
    }

}


$(document).ready(
    $('#add_tag_button').click(function () {

        const tagValue = $('#tagValue').val()
        if (tagValue.trim() === '') {
            alert('Tag input can not be empty')
        } else {
            $.ajax({
                type: 'POST',
                url: $(this).attr('action'),
                data: {
                    tag_name: tagValue,
                    csrfmiddlewaretoken: getCookie('csrftoken')
                },
                success: function (response) {
                    $('#tagValue').val('');
                    pushNewTagToTable(tagValue)
                }
            });
        }
    })
)

