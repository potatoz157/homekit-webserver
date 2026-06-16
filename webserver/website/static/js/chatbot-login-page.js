const loginForm = document.getElementById("login-form");

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    // extract the form data using built-in FormData api
    const formData = new FormData(loginForm);

    // conver the form data to a javascript object
    const data = Object.fromEntries(formData.entries());
    // console.log(data)
    const dataUrlPath = "/chatbot/login-validation"

    // WARNING!!!! ENCRYPT THE PASSWORD HERE PRIOR TO MAKING POST REQUEST!
    // YOU ARE CURRENTLY SENDING RAW PASSWORD TO BACKEND!

    try {
        const response = await fetch(dataUrlPath, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.status == "logged-in") {
            alert("Login Successful");
            window.location.href = '/chatbot/' // redirect user back to chatbot page
            
        } else {
            alert("Login Failed: " + result.message);
        }
    }
    catch (error) {
        console.error("Network Error: ", error)
        alert("Something went wrong. Please try again.")
    }


})