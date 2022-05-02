var sessionId;

var currentPath = "/";
var objectLimit = 10;
var loadedObjects = [];
var rightNowIsWhiteMode = true;
var savedDirectories = {};

async function createSession() {
    var newSession = await fetch('/api/v2/sessions', {
        method: 'PUT'
    });
    var jsonSession = await newSession.json();
    sessionId = jsonSession.sessionId;
}

async function loadDirFile(skip, generateContentAuthorization) {
	if (savedDirectories.hasOwnProperty(currentPath)) {
		var savedDirectory = savedDirectories[currentPath];
		if (savedDirectory.skip === skip &&
			savedDirectory.generateContentAuthorization === generateContentAuthorization) {
			loadedObjects = savedDirectory.loadedObjects;
			return savedDirectory.hasMore;
		}
	}
	
    var response = await fetch(`/api/v2/objects/check-directory?path=${currentPath}&skip=${skip}&limit=${objectLimit}&generateContentAuthorization=${(generateContentAuthorization ? "True" : "False")}`, {
        headers: {
            'x-session-id': sessionId
        }
    });
    var data = await response.json();

    if (skip > 0) {
        loadedObjects = new Array().concat(loadedObjects, data.objects);
    } else {
        loadedObjects = data.objects;
    }
	
	savedDirectories[currentPath] = {
		loadedObjects: JSON.parse(JSON.stringify(loadedObjects)),
		hasMore: data.hasMore,
		skip: skip,
		generateContentAuthorization: generateContentAuthorization
	};

    return data.hasMore;
}

function goToFile(file) {
    if (file.url.startsWith("/private/")) {
        if (!file.authorizedUrl || file.cannotGenerateLink) {
            alertMessage("Website can't generate url. Very sorry! :(", "danger", document.getElementById('live-alert'))
        } else {
            window.open(file.authorizedUrl, '_blank').focus();
        }
    } else {
        window.open("https://jd-s3.akamaized.net" + file.url, '_blank').focus();
    }
}

function generateFileList(hasMore) {
    var list = document.createDocumentFragment();
    if (currentPath != "/") {
        var li = createLi("🔙 Back");
        li.addEventListener("click", async function () {
            var currentPathSplitted = currentPath.split("/");

			var oldPath = currentPath.replace(currentPathSplitted[currentPathSplitted.length - 2], "");
            oldPath = oldPath.substring(0, oldPath.length - 1);
			
			currentPath = oldPath;
			
			var ul = document.getElementById("file-list");

            ul.innerHTML = "";
            ul.appendChild(createSpinner());

            var hasMore = await loadDirFile(0, true);
            var list = generateFileList(hasMore);

            ul.innerHTML = "";
            ul.appendChild(list);
        });
		
		list.appendChild(li);
    }

    loadedObjects.map(function (file) {
        var li = createLi(getEmojiByFile(file) + " " + file.name);

        if (file.type == "folder") {
            li.addEventListener('click', function () {
                goToThisPath(file.url);
            });
        } else {
            li.addEventListener('click', function () {
                goToFile(file);
            });
        }

        list.appendChild(li);
    });

    if (hasMore) {
        var moreList = createLi("⚓ Get more items");
        moreList.addEventListener("click", async function () {
            var ul = document.getElementById("file-list");

            ul.innerHTML = "";
            ul.appendChild(createSpinner());

            var hasMore = await loadDirFile(loadedObjects.length, true);
            var list = generateFileList(hasMore);

            ul.innerHTML = "";
            ul.appendChild(list);
        });

        list.appendChild(moreList);
    }

    return list;
}

async function goToThisPath(path) {
    var ul = document.getElementById("file-list");
    var pathValue = document.getElementById("path-value");

    pathValue.value = path;
    currentPath = path;

    ul.innerHTML = "";
    ul.appendChild(createSpinner());

    var hasMore = await loadDirFile(0, true);
    var list = generateFileList(hasMore);

    ul.innerHTML = "";
    ul.appendChild(list);
}

document.getElementById("go-to-this-path").addEventListener("click", function () {
    var newPath = document.getElementById("path-value").value;
    goToThisPath(newPath);
});

document.getElementById("change-theme").addEventListener("click", function () {
    if (rightNowIsWhiteMode) {
        document.getElementById("change-theme").innerHTML = 'Change to white theme';

        document.getElementById("body-html").classList.add("bg-dark");
        document.getElementById("body-html").classList.add("text-white");

        document.getElementById("list-card").classList.add("bg-dark");
        document.getElementById("list-card").classList.add("text-white");

        rightNowIsWhiteMode = false;
    } else {
        document.getElementById("change-theme").innerHTML = 'Change to dark theme';

        document.getElementById("body-html").classList.remove("bg-dark");
        document.getElementById("body-html").classList.remove("text-white");

        document.getElementById("list-card").classList.remove("bg-dark");
        document.getElementById("list-card").classList.remove("text-white");

        rightNowIsWhiteMode = true;
    }
});

setInterval(async function () {
    await fetch('/api/v2/ping', {
        headers: {
            'x-session-id': sessionId
        }
    });
}, 5000);

createSession()
.then(() => goToThisPath(currentPath));
