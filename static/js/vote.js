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

const clearMessage = (element) => {
  element.hidden = true;
};

ready(() => {
  const message = document.getElementById("vote-message");
  const categoryForms = document.querySelectorAll(".vote-form");
  const refreshButtons = document.querySelectorAll("button[data-refresh]");
  const contestContainer = document.querySelector(".category-vote-list");
  const contestSlug = contestContainer?.dataset.contest;

  if (!message || categoryForms.length === 0 || !contestSlug) {
    return;
  }

  let photoCache = [];
  const buildUrl = (path) => `${path}?contest=${encodeURIComponent(contestSlug)}`;

  const renderCategory = (categoryId) => {
    const grid = document.querySelector(`[data-category-grid="${categoryId}"]`);
    if (!grid) {
      return;
    }

    const entries = photoCache.filter((photo) => photo.categories.includes(categoryId));

    if (entries.length === 0) {
      grid.innerHTML = `<p class="empty-state">No entries yet. Encourage the crew to upload!</p>`;
      return;
    }

    grid.innerHTML = entries
      .map((photo) => {
        const votes = (photo.votes && photo.votes[categoryId]) ? photo.votes[categoryId] : 0;
        return `
          <article class="photo-card">
            <div class="vote-radio">
              <input type="radio" name="vote-${categoryId}" value="${photo.id}">
              <span>${votes} vote${votes === 1 ? "" : "s"}</span>
            </div>
            <img src="${photo.image_url}" alt="${photo.caption || "Halloween entry"}">
            <div class="details">
              <strong>${photo.uploader_name}</strong>
              ${photo.caption ? `<div class="caption">${photo.caption}</div>` : ""}
              <div class="meta">Submitted ${new Date(photo.created_at).toLocaleString()}</div>
            </div>
          </article>
        `;
      })
      .join("");
  };

  const renderAll = () => {
    const categories = Array.from(categoryForms).map((form) => form.dataset.category);
    categories.forEach(renderCategory);
  };

  const loadPhotos = async () => {
    const placeholders = document.querySelectorAll(".photo-grid .empty-state");
    placeholders.forEach((element) => {
      element.textContent = "Loading entries…";
    });

    try {
      const response = await fetch(buildUrl("/api/photos"));
      const data = await response.json();
      if (!response.ok) {
        throw new Error("Unable to load photos right now.");
      }
      photoCache = data.photos || [];
      renderAll();
    } catch (error) {
      setMessage(message, error.message, "error");
    }
  };

  categoryForms.forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearMessage(message);

      const categoryId = form.dataset.category;
      const selected = form.querySelector(`input[name="vote-${categoryId}"]:checked`);
      const submitButton = form.querySelector('button[type="submit"]');

      if (!selected) {
        setMessage(message, "Pick a favorite before you submit your vote.", "error");
        return;
      }

      submitButton.disabled = true;
      submitButton.textContent = "Submitting…";

      try {
        const response = await fetch("/api/votes", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            category: categoryId,
            photo_id: Number(selected.value),
          }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Vote not counted. Please try again.");
        }

        setMessage(message, "Vote recorded! Keep the spooky spirit alive.", "success");
        await loadPhotos();
      } catch (error) {
        setMessage(message, error.message, "error");
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Submit Vote";
      }
    });
  });

  refreshButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      clearMessage(message);
      await loadPhotos();
    });
  });

  loadPhotos();
});
