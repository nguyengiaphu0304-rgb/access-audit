const buttons = [...document.querySelectorAll("[data-filter]")];
const rows = [...document.querySelectorAll("tbody tr")];
const status = document.querySelector("#result-count");
const empty = document.querySelector("#empty");
for (const button of buttons) {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    for (const candidate of buttons) candidate.setAttribute("aria-pressed", String(candidate === button));
    let shown = 0;
    for (const row of rows) {
      const visible = filter === "all" || row.dataset.severity === filter;
      row.hidden = !visible;
      if (visible) shown += 1;
    }
    status.textContent = `${shown} findings shown`;
    empty.hidden = shown !== 0;
  });
}
