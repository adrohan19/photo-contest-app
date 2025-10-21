const ready = (handler) => {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", handler);
  } else {
    handler();
  }
};

const setMessage = (element, text, tone = "info") => {
  element.textContent = text;
  element.className = `alert ${tone}`;
  element.hidden = false;
};

ready(() => {
  const form = document.getElementById("upload-form");
  const message = document.getElementById("upload-message");

  if (!form || !message) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.hidden = true;

    const formData = new FormData(form);
    const categories = formData.getAll("categories");

    if (categories.length === 0) {
      setMessage(message, "Pick at least one superlative before sharing your masterpiece.", "error");
      return;
    }

    try {
      const response = await fetch("/api/photos", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Upload failed. Please try again.");
      }

      form.reset();
      setMessage(message, data.message || "Photo submitted! Start hyping the votes.", "success");
    } catch (error) {
      setMessage(message, error.message, "error");
    }
  });
});
