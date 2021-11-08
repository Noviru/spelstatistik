function myFunction(loop) {
   $("#moreStats_"+loop).slideToggle();
}




function handle(e){

    if (e.keyCode == 13) {
        var input = document.getElementById("input").value;
        input.submit();
        }
}




