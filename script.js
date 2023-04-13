function showAlert(title, message) {
  var customAlert = document.getElementById("customAlert");
  var customAlertTitle = document.getElementById("customAlertTitle");
  var customAlertText = document.getElementById("customAlertText");
  customAlertTitle.innerHTML = title;
  customAlertText.innerHTML = message;
  customAlert.style.display = "block";
}

function closeCustomAlert() {
  var customAlert = document.getElementById("customAlert");
  customAlert.style.display = "none";
}