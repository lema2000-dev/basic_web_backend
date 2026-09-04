const button = document.querySelector(
    "#load-message"
);

const message = document.querySelector(
    "#message"
);

button.addEventListener("click", async () => {
    message.textContent = "Loading...";

    try {
        const response = await fetch(
            "/api/message?name=Martin"
        );

        if (!response.ok) {
            throw new Error(
                `HTTP error: ${response.status}`
            );
        }

        const data = await response.json();

        message.textContent = data.message;
    } catch (error) {
        message.textContent =
            "The message could not be loaded.";

        console.error(error);
    }
});