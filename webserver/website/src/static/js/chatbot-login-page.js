
document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const loginForm = document.getElementById("login-form");

    // extract the form data using built-in FormData api
    const formData = new FormData(loginForm);

    // conver the form data to a javascript object
    const data = Object.fromEntries(formData.entries());
    const dataUrlPath = "/chatbot/login-validation"


    try {
        const response = await fetch(dataUrlPath, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.status == "success") {
            alert("Login Successful");
            window.location.href = '/chatbot/' // redirect user back to chatbot page
            
        } else {
            document.getElementById("login-error-message").style.display = "block";
            // alert("Login Failed: " + result.message);
        }
    }
    catch (error) {
        console.error("Network Error: ", error)
        alert("Something went wrong. Please try again.")
    }

});


document.getElementById("username").addEventListener("input", function() {
    document.getElementById("login-error-message").style.display = "none";
});


document.getElementById("password").addEventListener("input", function() {
    document.getElementById("login-error-message").style.display = "none";
});