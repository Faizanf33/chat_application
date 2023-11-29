// set on click event for show hide password icon fa-eye-slash fa-eye
$(document).on("click", ".fa", function () {
  if ($(this).hasClass("fa-eye-slash")) {
    $(this).removeClass("fa-eye-slash");
    $(this).addClass("fa-eye");
    $("#login_password").attr("type", "text");
  } else {
    $(this).removeClass("fa-eye");
    $(this).addClass("fa-eye-slash");
    $("#login_password").attr("type", "password");
  }
});
