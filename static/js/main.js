function scroll_to_id() {
    $('a[href^="#"]').on('click.smoothscroll', function(e) {
        e.preventDefault();
        var target = this.hash,
            $target = $(target);
        $('html, body').stop().animate({
            'scrollTop': $target.offset().top - 150
        }, 500, 'swing');
    });
}

// Инициализируем функцию при загрузке DOM
$(document).ready(function() {
    scroll_to_id();
});
