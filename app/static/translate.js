function translate(destId, sourceId, destLang, sourceLang) {
    let sourceField = document.getElementById(sourceId)
    let destField = document.getElementById(destId)
    let post = JSON.stringify({
        text: sourceField.textContent,
        dest_language: destLang,
        source_language: sourceLang
    })

    destField.innerHTML = '<div class="spinner-grow text-info" style="width: 1.3rem; height: 1.3rem;" role="status">' +
        '<span class="visually-hidden">Loading...</span> </div>'

    fetch('/translate', {
        method: 'POST',
        body: post,
        headers: {
            'Content-Type': 'application/json'
        },
    }).then((response) => {
        if (response.ok) {
            return response.json()
        } else {
            return Promise.reject(response)
        }
    }).then((data) => {
        destField.innerHTML = data['text'].toString()
    }).catch((error) => {
        destField.innerHTML = '<small class="text-danger"> Something went wrong: ' + error.statusText + '</small>'
    });
}
