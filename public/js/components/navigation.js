export function updateNavigation(view) {
  document.querySelectorAll("[data-view]").forEach((button) => {
    const active = button.dataset.view === view;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  const copy = {
    home: [
      "A little closer, every day",
      "Fresh perspectives. Familiar faces. Your kind of community.",
    ],
    explore: [
      "Find your next inspiration",
      "Discover ideas and people a little outside your everyday.",
    ],
    saved: [
      "Your little collection",
      "The moments and ideas you want to come back to.",
    ],
  }[view];
  const title = document.querySelector("#view-title");
  title.textContent = copy[0];
  const dot = document.createElement("span");
  dot.textContent = ".";
  title.append(dot);
  document.querySelector("#view-description").textContent = copy[1];
  document.querySelector(".composer").hidden = view !== "home";
  document.querySelector(".feed-tabs").hidden = view === "saved";
}
