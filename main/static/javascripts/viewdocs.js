$(document).ready(function() {
    $('#btnHide').click(function() {
      $('td:nth-child(7),th:nth-child(7)').toggle()
    });

});

$('body').on('click', function (e) {
    //did not click a popover toggle or popover
    if ($(e.target).data('toggle') !== 'popover'
        && $(e.target).parents('.popover.in').length === 0) {
        $('[data-toggle="popover"]').popover('hide');
    }
});

$('[data-toggle="popover"]').each( function() {
  $(this).popover({
                    html : true,
                    content: $(this).next().html()
                 });
  });

$('[data-toggle="popover"]').click(function(e) {
  $('[data-toggle="popover"]').not(this).popover('hide');
})
