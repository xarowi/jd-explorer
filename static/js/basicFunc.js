function createSpinner() {
    var center = document.createElement('center');
    var spinner = document.createElement('div');

    spinner.classList.add("spinner-border");
    spinner.classList.add("text-danger");

    center.appendChild(spinner);

    return center;
}

function createLi(innerText) {
    let li = document.createElement('li');

    li.classList.add("list-group-item");
    li.classList.add("list-group-item-action");

    li.innerHTML = innerText;

    return li;
}

function getEmojiByFile(file) {
    if (file.type === "folder") {
        return "📂";
    } else if (file.type === "file") {
        if (file.name.endsWith(".webm")) {
            return "🎞️";
        } else if (file.name.endsWith(".ogg") || file.name.endsWith(".opus")) {
            return "🎵";
        } else if (file.name.endsWith(".png") || file.name.endsWith(".jpg")) {
            return "🖼️";
        } else {
			return "📜";
		}
    }
	return "💀";
}

function alertMessage(message, type, placeholder) {
    var wrapper = document.createElement('div');
    wrapper.innerHTML = '<div class="alert alert-' + type + ' alert-dismissible" role="alert">' + message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';

    placeholder.append(wrapper);
}
