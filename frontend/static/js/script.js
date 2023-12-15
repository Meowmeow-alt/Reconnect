document.addEventListener('DOMContentLoaded', function() {
    let logout = document.querySelector("#logout");

    logout.addEventListener('click', function(event) {
        let confirmation = confirm("Are you sure you want to log out?");
    
        if (!confirmation) {
            event.preventDefault();
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    let del = document.querySelector("#delete");

    del.addEventListener('click', function(event) {
        let confirmation = confirm("Are you sure you want to delete this profile?");
    
        if (!confirmation) {
            event.preventDefault();
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    let accept = document.querySelector("#accept");
    accept.addEventListener('click', function(event) {
        let confirmation = confirm("Are you sure you want to accept this match?");
    
        if (!confirmation) {
            event.preventDefault();
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    let decline = document.querySelector("#decline");
    decline.addEventListener('click', function(event) {
        let confirmation = confirm("Are you sure you want to decline this match?");
    
        if (!confirmation) {
            event.preventDefault();
        }
    });
});

function momodal(index){
    var modal = document.getElementById("nenmodal-1");
    var contentContainer = document.getElementById("contentContainer"); // Get the new content container
    modal.classList.toggle("active");

    // If the modal is being opened, populate the content
    if (modal.classList.contains("active")) {
        var info = infos[index];
        contentContainer.innerHTML = `
            <p style="color: black;">
                Name: ${info['name']}<br>
                Username: ${info['username']}<br>
                Age: ${info['age']}<br>
                Gender: ${info['biological_sex'] == 0 ? "Female" : "Male"}<br>
                Phone: ${info['phone']}<br>
                Mail: ${info['mail']}
            </p>
        `;
    }
}


