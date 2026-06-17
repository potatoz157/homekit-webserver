const registrationForm = document.getElementById("register-form");

registrationForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const usernameField = document.getElementById("username");
    const confirmPasswordField = document.getElementById("confirm_password");

    // clear any existing errors
    // usernameField.setCustomValidity(""); // clear the existing user error message
    // confirmPasswordField.setCustomValidity("");    // clear the error message

    // extract the form data using built-in FormData api
    const formData = new FormData(registrationForm);
    const data = Object.fromEntries(formData.entries()); // convert the form data to a javascript object
    

    console.log(data);

    if (data.password !== data.confirm_password) {
        // set the error message on the confirm password input field
        confirmPasswordField.setCustomValidity("Passwords do not match.");

        // show the popup immediately
        confirmPasswordField.reportValidity();
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
        console.log(result.status == "error-user-exists");
        // if a user was successfully added, redirect the user (user should be logged in upon registration -- this is handled in backend)
        if (result.status == "success") {
            alert("Registration Successful");
            window.location.href = '/chatbot/' // redirect user back to chatbot page
            return;
        }
        else if (result.status == "error-user-exists") {
            
            // REPLACE THE VALIDITY MESSAGES WITH A CUSTOM TEXT MESSAGE ELEMENT (e.g. <h4> tag) SET INSIDE THE HTML
            // SIMPLY TRIGGER THE DISPLAY ON/OFF AS NEEDED
            // THE CURRENT IMPLEMENTATION DOES NOT PROPERLY BRING THE POPUP FOR EXISTING USERNAMES
            // -- DO THIS FOR BOTH THE REGISTRATION PAGE AND LOGIN PAGE!!!!!!!!!!!!!

            usernameField.setCustomValidity("Username already exists.");
            usernameField.reportValidity();
            return;
        }
    
    }
    catch (error) {
        console.error("Network Error: ", error)
    }


});


// 1. Clear the username error as soon as the user changes their username
document.getElementById("username").addEventListener("input", function() {
    this.setCustomValidity("");
});

// 2. Clear the password errors as soon as they type in either password field
document.getElementById("password").addEventListener("input", function() {
    document.getElementById("confirm_password").setCustomValidity("");
});

document.getElementById("confirm_password").addEventListener("input", function() {
    this.setCustomValidity("");
});