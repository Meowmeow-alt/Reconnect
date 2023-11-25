document.addEventListener('DOMContentLoaded', function() {
    let logout = document.querySelector("#logout");

    logout.addEventListener('click', function(event) {
        let confirmation = confirm("Are you sure you want to log out?");
    
        if (!confirmation) {
            event.preventDefault();
        }
    });

    let del = document.querySelector("#delete");

    del.addEventListener('click', function(event) {
        let confirmation = confirm("Are you sure you want to delete this profile?");
    
        if (!confirmation) {
            event.preventDefault();
        }
    });

});
