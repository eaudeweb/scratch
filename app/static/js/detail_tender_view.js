
function pushNewTagToTable(tagInputValue) {
    const tagsList = document.querySelector('#tags_list_displayed')
    const tagsListValues = tagsList.innerText.split(',')

    tagsListValues.push(tagInputValue)

    const filteredArr = tagsListValues.filter(function (element) {
        return element !== '';
    });

    tagsList.innerHTML = filteredArr.join(', ')
}




function pushTagDb(id, tagInputValue) {
    console.log(id)
    $.ajax({
        type: 'POST',
        url: `/tenders/tag/${id}/`,
        data: {
            tag_name: tagInputValue,
            csrfmiddlewaretoken: getCookie('csrftoken')
        },
        success: function (response) {
            console.log(response)
            document.querySelector('#tagValue').value = ''

        }
    });
}


function addTagToTender(tender_id) {
    const tagInputValue = document.querySelector('#tagValue').value

    if (tagInputValue.trim() == '') {
        alert('Tag input can not be empty')
    } else {
        pushNewTagToTable(tagInputValue)
        pushTagDb(tender_id, tagInputValue)

    }
}
