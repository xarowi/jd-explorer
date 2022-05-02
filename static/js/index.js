var alertPlaceholder = document.getElementById('live-alert');
var goToButton = document.getElementById("go-to-this-path");

function createSpinner() {
	var center = document.createElement('center');
	var spinner = document.createElement('div');
	
	spinner.classList.add("spinner-border");
	spinner.classList.add("text-danger");
	
	center.appendChild(spinner);
	
	return center;
}

function createGoBackLi(currentPath) {
	let li = document.createElement('li');
	
	li.classList.add("list-group-item");
	li.classList.add("list-group-item-action");
	
	var currentPathSplitted = currentPath.split("/");
	
	var oldPath = currentPath.replace(currentPathSplitted[currentPathSplitted.length - 2], "");
	oldPath = oldPath.substring(1, oldPath.length - 1);
	
	li.addEventListener('click', function () {
		goToThisPath(oldPath);
	});
	
	li.innerHTML = "🔙 Back";
	
	return li;
}

function alert(message, type) {
	var wrapper = document.createElement('div');
	wrapper.innerHTML = '<div class="alert alert-' + type + ' alert-dismissible" role="alert">' + message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';

	alertPlaceholder.append(wrapper);
}

function moveToThisFile(url) {
	var request = new XMLHttpRequest();
	
    request.open('GET', '/api/v1/get-download-url?url=' + url);
    request.send();
	
    request.onload = function () {
		console.log(this.response);
		
		if (this.response.includes("429 Too Many Requests")) {
			alert("Too many requests. Cool down!", "warning");
		}
		
        var response = JSON.parse(this.response);
		
		if (response.move) {
			window.open(response.url, '_blank').focus();
		}
		
		if (response.message) {
			alert(response.message, "danger");
		}
	};
}

function goToThisPath(path) {
	var ul = document.getElementById("file-list");
	var pathValue = document.getElementById("path-value");
	pathValue.value = "/" + path;
	
	ul.innerHTML = "";
	ul.appendChild(createSpinner());
	
    var request = new XMLHttpRequest();
	
    request.open('GET', '/api/v1/file-list?path=' + path);
    request.send();
	
    request.onload = function () {
        var response = JSON.parse(this.response);
		var list = document.createDocumentFragment();
		
		if (pathValue.value != "/") {
			list.appendChild(createGoBackLi(pathValue.value));
		}
		
		response.items.map(function (file) {
			let li = document.createElement('li');
			
			li.classList.add("list-group-item");
			li.classList.add("list-group-item-action");
			
			if (file.type == "folder") {
				li.addEventListener('click', function () {
					goToThisPath(file.url);
				});
			} else {
				li.addEventListener('click', function () {
					moveToThisFile(file.url);
				});
			}
			
			if (file.type == "folder") {
				li.innerHTML = "📂 " + file["name"]; 
			} else if (file.type == "file" && file.name.endsWith(".webm")) {
				li.innerHTML = "🎞️ " + file["name"]; 
			} else if (file.type == "file" && (file.name.endsWith(".ogg") || file.name.endsWith(".opus"))) {
				li.innerHTML = "🎵 " + file["name"]; 
			} else if (file.type == "file" && (file.name.endsWith(".png") || file.name.endsWith(".jpg"))) {
				li.innerHTML = "🖼️ " + file["name"]; 
			} else {
				li.innerHTML = "📜 " + file["name"]; 
			}
			
			list.appendChild(li);
		});
		
		ul.innerHTML = "";
		ul.appendChild(list);
    }
}

goToButton.addEventListener('click', function () {
	var path = document.getElementById("path-value").value.substring(1);
	goToThisPath(path);
});

goToThisPath("");