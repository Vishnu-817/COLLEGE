const menuToggle = document.querySelector(".menu-toggle");
const primaryNav = document.querySelector("#primary-nav");

menuToggle?.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
  primaryNav?.classList.toggle("is-open", !isOpen);
});

primaryNav?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    menuToggle?.setAttribute("aria-expanded", "false");
    menuToggle?.setAttribute("aria-label", "Open navigation");
    primaryNav.classList.remove("is-open");
  });
});

const programSearch = document.querySelector("#program-search");
const programCards = [...document.querySelectorAll(".program-card")];
const noResults = document.querySelector("#no-results");
const filterButtons = [...document.querySelectorAll(".filter-button")];
let selectedLevel = "all";

function filterPrograms() {
  const query = programSearch.value.trim().toLocaleLowerCase();
  let visibleCount = 0;
  for (const card of programCards) {
    const matchesText = card.dataset.program.includes(query);
    const matchesLevel = selectedLevel === "all" || card.dataset.level === selectedLevel;
    const visible = matchesText && matchesLevel;
    card.hidden = !visible;
    if (visible) visibleCount += 1;
  }
  noResults.hidden = visibleCount !== 0;
}

programSearch?.addEventListener("input", filterPrograms);
filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    selectedLevel = button.dataset.level;
    filterButtons.forEach((item) => {
      const selected = item === button;
      item.classList.toggle("active", selected);
      item.setAttribute("aria-pressed", String(selected));
    });
    filterPrograms();
  });
});

document.querySelectorAll(".flash button").forEach((button) => {
  button.addEventListener("click", () => button.closest(".flash").remove());
});
