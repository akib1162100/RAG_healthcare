$(document).ready(function () {
    if(localStorage.getItem("is_night_mode") && localStorage.getItem("is_night_mode") == 't'){
        $('.o_web_client').addClass('sh_night_mode');
    }else{
        $('.o_web_client').removeClass('sh_night_mode');
    }
    $(document).on("click", ".sh_close_notification", function () {
        $("#object").css("display", "none");
        $("#object1").css("display", "none");
    });
   
    

    // $('body').keydown(function (e) {
    //     if ($("body").hasClass("sh_sidebar_background_enterprise")) {
    //         $(".sh_search_container").css("display", "block");
    //         $(".usermenu_search_input").focus();
    //         $(".sh_backmate_theme_appmenu_div").css("opacity", "0")
    //         if(!$("body").hasClass("sh_detect_first_keydown")){
    //             $(".usermenu_search_input").keydown()
    //         }
         
    //     }
    // });

});