// Keep asset failures explicit without exposing exception details to the UI.
try {
  await import("./app.mjs");
} catch {
  const view = document.querySelector("#view");
  const section = document.createElement("section");
  section.className = "empty";
  section.setAttribute("role", "alert");
  const heading = document.createElement("h1");
  heading.textContent = "The preview could not start";
  const message = document.createElement("p");
  message.textContent = "A required app file could not load. Reload to try again. No live data was accessed.";
  const retry = document.createElement("button");
  retry.className = "primary";
  retry.dataset.testid = "button-retry";
  retry.textContent = "Reload preview";
  retry.addEventListener("click", () => location.reload());
  section.append(heading, message, retry);
  view.replaceChildren(section);
}
