const registrationForm = document.getElementById("register-form");

registrationForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const usernameField = document.getElementById("username");

    // extract the form data using built-in FormData api
    const formData = new FormData(registrationForm);
    const data = Object.fromEntries(formData.entries()); // convert the form data to a javascript object


    if (data.password !== data.confirm_password) {
        document.getElementById("confirm-pass-field-error-msg").style.display = "block"; // show the passwords do not match error
        return; // exit immediately
    }

    try {
        // now that the passwords are valid, send a post request with the username and password
        // check the response to see if the username already exists
        const dataUrlPath = "/chatbot/create-account";
        const response = await fetch(dataUrlPath, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
    
        const result = await response.json();
        console.log(result.status);
        // if a user was successfully added, redirect the user (user should be logged in upon registration -- this is handled in backend)
        if (result.status == "success") {
            alert("Registration Successful");
            window.location.href = '/chatbot/' // redirect user back to chatbot page
            return;
        }
        else if (result.status == "error-user-exists") {
            const usernameErrorLabel = document.getElementById("username-field-error-msg");
            usernameErrorLabel.style.display = "block";
            return;
        }
    
    }
    catch (error) {
        console.error("Network Error: ", error)
    }


});

// clear the username error the moment anything is typed into the username field
document.getElementById("username").addEventListener("input", function() {
    document.getElementById("username-field-error-msg").style.display = 'none';

});

document.getElementById("password").addEventListener("input", function() {

    document.getElementById("pass-field-error-msg").style.display = 'none';
    document.getElementById("confirm-pass-field-error-msg").style.display = 'none';

});

document.getElementById("confirm_password").addEventListener("input", function() {

    document.getElementById("pass-field-error-msg").style.display = 'none';
    document.getElementById("confirm-pass-field-error-msg").style.display = 'none';
    
});