let elements = Array.from(document.querySelectorAll('[data-username]'))
elements.forEach((element) => {
    let username = element.getAttribute('data-username')
    tippy(element, {
        interactive: true,
        animation: 'shift-away-subtle',
        theme: 'light',
        placement: 'left',
        allowHTML: true,
        delay: [800, 200],
        onShow(instance) {
            fetch('/profile/' + username + '/popup')
                .then((response) => response.text())
                .then((html) => {
                    instance.setContent(html)
                    flask_moment_render_all();
                })
                .catch((error) => {
                    instance.setContent(`Request failed. ${error}`);
                });
        }
    })
})