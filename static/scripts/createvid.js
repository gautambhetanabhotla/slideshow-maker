document.getElementById("create_video_button").addEventListener("click", function () {
    var selectedFiles = document.querySelectorAll('input[name^="chkbox"]:checked');
    if (selectedFiles.length === 0) {
        alert("Please select at least one file before creating a video.");
        return;
    }

    var fileNames = [];
    selectedFiles.forEach(function (file) {
            var label = file.nextElementSibling;
            var imgSrc = label.querySelector('img').src;
            var fileName = imgSrc.split('/').pop(); // Extract the file name
            fileNames.push(fileName);
        }
    );

    fetch('/move_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ files: fileNames }),
    })    
    .then(response => {
        if (response.ok) {
            window.location.href = "/video";
        } else {
            alert('Failed to move files.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});