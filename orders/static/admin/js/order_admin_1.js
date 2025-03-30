document.addEventListener("DOMContentLoaded", function () {
    // Ensure this script runs after Select2 is initialized
    jQuery(document).ready(function ($) {
        
       $(document).find('.field-get_assigned_to_name').each(function(){
              let parent = $(this).parents('tr');
              if($(this).text()=="No Assigned User" || $(this).text()=="Unassigned, Order"){
                  parent.addClass('bg-red');
              }

            });
    });

});
