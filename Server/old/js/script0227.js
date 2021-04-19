$(function(){
    $('#genre_btn').click(function(){
        $('#genre').toggle();
    });
    $('#genre_detail').css('font-size','100%');
    $('#errorA').click(function(){
        $('#correctA').toggle();
    });
    $('#errorB').click(function(){
        $('#correctB').toggle();
    });
    $('#errorA').css('color','red').css('font-weight','bold').css('font-size','200%');
    $('#errorB').css('color','blue').css('font-weight','bold').css('font-size','200%');

});
