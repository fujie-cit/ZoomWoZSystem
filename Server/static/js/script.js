$(function(){
    $('#genre_btn').click(function(){
        $('#genre').toggle();
    });
    $('#tipsA').click(function(){
        $('#tips_typeA').toggle();
    });
    $('#tipsB').click(function(){
        $('#tips_typeB').toggle();
    });
    $('#tips_typeA').css('color','red').css('font-weight','bold').css('font-size','250%');
    $('#tips_typeB').css('color','blue').css('font-weight','bold').css('font-size','250%');

});
