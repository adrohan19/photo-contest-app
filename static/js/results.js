const ready = (handler) => {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", handler);
  } else {
    handler();
  }
};

ready(() => {
  const blocks = document.querySelectorAll("[data-results-list]");
  const grid = document.getElementById("results-grid");
  const contestSlug = grid?.dataset.contest;
  if (blocks.length === 0 || !contestSlug) {
    return;
  }

  const buildUrl = (path) => `${path}?contest=${encodeURIComponent(contestSlug)}`;

  const render = (categoryId, entries) => {
    const list = document.querySelector(`[data-results-list="${categoryId}"]`);
    if (!list) {
      return;
    }

    if (!entries || entries.length === 0) {
      list.innerHTML = `<li class="empty-state">No votes yet. Rally your fans!</li>`;
      return;
    }

    list.innerHTML = entries
      .map(
        (entry) => `
          <li>
            <strong>${entry.uploader_name}</strong>
            <span>${entry.caption || "No caption provided."}</span>
            <span>${entry.votes} vote${entry.votes === 1 ? "" : "s"}</span>
          </li>
        `
      )
      .join("");
  };

  const loadResults = async () => {
    try {
      const response = await fetch(buildUrl("/api/results"));
      const data = await response.json();
      if (!response.ok) {
        throw new Error("Could not load results.");
      }

      blocks.forEach((block) => {
        const categoryId = block.dataset.resultsList;
        render(categoryId, data.results?.[categoryId]);
      });
    } catch (error) {
      console.error(error);
    }
  };

  loadResults();
  setInterval(loadResults, 20000);
});
