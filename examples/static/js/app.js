const form = document.querySelector(
    "#message-form"
);

const nameInput = document.querySelector(
    "#name"
);

const message = document.querySelector(
    "#message"
);

form.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        message.textContent = "Loading...";

        try {
            const response = await fetch(
                "/api/message",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        name: nameInput.value
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail
                    ?? `HTTP error: ${response.status}`
                );
            }

            message.textContent = data.message;
        } catch (error) {
            message.textContent =
                "The message could not be loaded.";

            console.error(error);
        }
    }
);