
function previewImage(obj) {
    const fileReader = new FileReader();
    fileReader.onload = (function () {
        document.getElementById("thumbnail-preview").src = fileReader.result;
    });
    fileReader.readAsDataURL(obj.files[0]);
}


// ...
// タイトルの文字数をカウント
function showTitleLength(str) {
    document.getElementById("title-form-length").textContent = str.length;
}

// 詳細文の文字数をカウント
function showDescriptionLength(str) {
    document.getElementById("description-form-length").textContent = str.length;
}