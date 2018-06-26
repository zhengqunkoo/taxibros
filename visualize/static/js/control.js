$(document).ready(function() {
    $("input[type='checkbox']").change(function() {
        if(this.checked) {
            $("#description-controls").css('color','#4a4a4a');
        } else {
            $("#description-controls").css('color','#cdcdcd');
        }
    });
});
