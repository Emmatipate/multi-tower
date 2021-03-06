$(document).ready(function(){
    // Modals
    $('#player_login').modal('setting', 'closable', false);
    $('#player_login').modal('show');

    $('#gameover_modal').modal('setting', 'closable', false);
    $('#gameover_modal').modal('hide');

    // Set focus after 100 ms
    setTimeout(function(){
        $('#player_name_text').focus()
    }, 100);

    tryLogin = function(event) {
        if ($('#player_name_text').val()){
            console.log("Player "+$('#player_name_text').val()+" enters");
            $('#player_login').modal('hide')
            event.stopPropagation();
            start().then(start2);
        }
    }

    $('#player_name_submit').click(function (e) { tryLogin(e) });
    $('#player_name_text').keypress(function (e) {
        if (e.which == 13){
            tryLogin(e);
        }
    });

    // Sidebar
    $('.sidebar')
        .sidebar({
            closable: false,
            dimPage: false
        })
        .sidebar('setting', 'transition', 'overlay')
        .sidebar('attach events','#sidebar_toggle')


    // Sidebar toggle
    $("#sidebar_toggle").state({text: {inactive:'<<', active:'>>'}});

    setInterval(function () {
        $("#sidebar_toggle").css("left", ($(".sidebar").position().left+$(".sidebar").width()+40+"px"));
    }, 10);

    // Add button - events
    $('#create_tower').click(function(){ adding = !adding; addingMode(); $('#create_tower').toggleClass('active');});
    $('#delete_tower').click(function(){  request_delete(selected.id); });
    $('#upgrade_tower').click(function(){ request_upgrade(selected.id); });
    $('#attack_castle').click(function(){ request_attack(selected.player_name); });
    if (selected.player_name == me) {
        $('#attack_castle').hide();
    }

    // Stop building on escape
    $(document).keyup(function(e) {
        if (e.keyCode == 27 && adding) { // escape key maps to keycode `27`
            adding = false; addingMode(); $('#create_tower').removeClass('active');
        }
    });


});

// Healthbar
function setHealthbar(value){
    $('#healthbar_container').progress({ percent: Math.max(value, 0) });
    $('#healthbar_text').text(value+"%");
}
