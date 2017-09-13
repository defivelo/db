// https://github.com/twbs/bootstrap/issues/16703#issuecomment-223420145
$('label.btn').click(function () {
    if ($(this).hasClass('disabled') || $(this).attr('disabled')) return false;
    return true;
});
