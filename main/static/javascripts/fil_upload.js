// Get the template HTML and remove it from the doumenthe template HTML and remove it from the doument
var previewNode = document.querySelector("#template");
previewNode.id = "";
var previewTemplate = previewNode.parentNode.innerHTML;
previewNode.parentNode.removeChild(previewNode);

var myDropzone = new Dropzone(document.body, { // Make the whole body a dropzone
    url: "", // Set the url
    thumbnailWidth: 80,
    thumbnailHeight: 80,
    parallelUploads: 20,
    previewTemplate: previewTemplate,
    autoQueue: false, // Make sure the files aren't queued until manually added
    previewsContainer: "#previews", // Define the container to display the previews
    clickable: ".fileinput-button",
    uploadMultiple: true

});

myDropzone.options.params = true;

myDropzone.on("addedfile", function (file) {
    filename = String(file.name);
    filenamesuffix = filename.substring(filename.lastIndexOf(".") + 1)

    if (filenamesuffix == 'pdf') {
        file.previewElement.querySelector("img").src = "/static/img/pdf.png";
    } else if (filenamesuffix.includes("xl")) {
        file.previewElement.querySelector("img").src = "/static/img/xlsx.png";
    } else if (filenamesuffix.includes("doc")) {
        file.previewElement.querySelector("img").src = "/static/img/docx.png";
    }
    file.previewElement.querySelector(".start").onclick = function () {
        myDropzone.enqueueFile(file);
    };

    //Ensure user does not edit out the file extension
    checkRename();

});

function checkRename() {

  var classname = document.getElementsByClassName("name");

  classname[classname.length - 1].addEventListener('input', function(filenamesuffix) {
    let rename = this.innerHTML;

    //check period
    let lastPeriodIndex = rename.lastIndexOf(".");
    let new_suffix = rename.substring(lastPeriodIndex + 1);
    if (lastPeriodIndex == -1) {
      alert("Please don't remove the file's extention!");
    }
  }, false);
}

myDropzone.on("totaluploadprogress", function (progress) {
    document.querySelector("#total-progress .progress-bar").style.width = progress + "%";
});


myDropzone.on("sending", function (file, xhr, formData) {
    document.querySelector("#total-progress").style.opacity = "1";
    file.previewElement.querySelector(".start").setAttribute("disabled", "disabled");
    formData.append("csrfmiddlewaretoken", $('input[name="csrfmiddlewaretoken"]').val());
});

myDropzone.on("queuecomplete", function (progress) {
    document.querySelector("#total-progress").style.opacity = "0";

});

document.querySelector("#actions .start").onclick = function () {
  start_upload("private");
};

function start_upload(type) {
  var names = '';
  files = myDropzone.getFilesWithStatus(Dropzone.ADDED);
  for (var each of files) {
    names += each.previewElement.querySelector(".name").innerHTML + '>'
  }

  myDropzone.options.url += ""; // modify url if needed
  myDropzone.enqueueFiles(files);
}


document.querySelector("#actions .cancel").onclick = function () {
    myDropzone.removeAllFiles(true);
};


$(document).ready(function () {
    $.when($.ajax({
        type: 'GET',
        url: 'get_settings'
    })).then(function (data) {
        json = $.parseJSON(data);
        myDropzone.options.acceptedFiles = json.ALLOWED_FILE_MIME_TYPES.join();
        $("#container").show();
    });

});
