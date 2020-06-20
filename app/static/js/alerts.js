function alarms(message) {

  $alarm =
    '<div class="alert alert-info alert-dismissible fade show " role="alert" style="position: fixed;top: 60px;right: 30px;">' +
    '<h4 class="alert-heading">Well done!</h4>' +
    '<hr>' +
    '<strong>'+ message +'</strong>'+
    '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
    '<span aria-hidden="true">&times;</span>' +
    '</button>' +
    '</div>'
  $("#alarm").html($alarm);
};

function error(message) {

  $alarm =
    '<div class="alert alert-danger alert-dismissible fade show w-25" role="alert" style="position: fixed;top: 60px;right: 30px;">' +
    '<h4 class="alert-heading">Well done!</h4>' +
    '<hr>' +
    '<strong>'+ message +'</strong>'+
    '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
    '<span aria-hidden="true">&times;</span>' +
    '</button>' +
    '</div>'
  $("#alarm").html($alarm);
};

function sus(message) {

  $alarm =
    '<div class="alert alert-success alert-dismissible fade show w-25" role="alert" style="position: fixed;top: 60px;right: 30px;">' +
    '<h4 class="alert-heading">Well done!</h4>' +
    '<hr>' +
    '<strong>'+ message +'</strong>'+
    '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
    '<span aria-hidden="true">&times;</span>' +
    '</button>' +
    '</div>'
  $("#alarm").html($alarm);
};
