const uploadForm = document.querySelector(
    "#upload-form"
);

const uploadResult = document.querySelector(
    "#upload-result"
);

uploadForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        uploadResult.textContent =
            "Uploading...";

        const formData = new FormData(
            uploadForm
        );

        try {
            const response = await fetch(
                "/api/upload",
                {
                    method: "POST",
                    body: formData
                }
            );

            if (!response.ok) {
                const errorBody =
                    await response.text();

                throw new Error(
                    `HTTP ${response.status}: `
                    + errorBody
                );
            }

            const data = await response.json();

            uploadResult.textContent =
                JSON.stringify(
                    data,
                    null,
                    2
                );
        } catch (error) {
            uploadResult.textContent =
                "The upload failed.";

            console.error(error);
        }
    }
);