let dropArea = document.getElementById('drop-area');
let fileElem = document.getElementById('fileElem');
let gallery = document.getElementById('gallery');
let formElem = document.getElementById('formElem');
let fd = new FormData(formElem);

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

formElem.onsubmit = async(e) => {
    e.preventDefault();
    
    let response = await fetch('/uploadimages', {
      method: 'POST',
      body: fd
    });

    location.reload();
    console.log(response.text());
  };

dropArea.addEventListener('drop', handleDrop, false);
// fileElem.addEventListener('change', handleChange, false);

function handleChange(e) {
    handleFiles(this.files);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    dropArea.classList.add('highlight');
}

function unhighlight(e) {
    dropArea.classList.remove('highlight');
}

function handleDrop(e) {
    let dt = e.dataTransfer;
    let files = dt.files;
    console.log(files);
    handleFiles(files);
}

dropArea.addEventListener('click', () => {
    fileElem.click();
});

fileElem.addEventListener('change', function (e) {
    console.log("changed ra");
    console.log(this.files);
    handleFiles(this.files);
});

function handleFiles(files) {
    files = [...files];
    files.forEach(previewFile);
    files.forEach(addToForm)
}

function previewFile(file) {
    let reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = function () {
        let img = document.createElement('img');
        img.src = reader.result;
        gallery.appendChild(img);
    }
}

function addToForm(file) {
    fd.append('file', file);
}

function DisplayData() {
    console.log(fd.getAll('file'));
}

setInterval(DisplayData, 1000);