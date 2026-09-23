// Keep asset failures explicit without exposing exception details to the UI.
const demo = new URLSearchParams(location.search).get("demo") === "1";
try {
  if (demo) {
    await import("./app.mjs");
  } else {
    await import("./research.mjs");
  }
} catch {
  const view = document.querySelector("#view");
  const section = document.createElement("section");
  section.className = "empty";
  section.setAttribute("role", "alert");
  const heading = document.createElement("h1");
  heading.textContent = demo ? "The preview could not start" : "The research app could not start";
  const message = document.createElement("p");
  message.textContent = "A required app file could not load. Reload to try again. No private data was accessed.";
  const retry = document.createElement("button");
  retry.className = "primary";
  retry.dataset.testid = "button-retry";
  retry.textContent = demo ? "Reload preview" : "Reload app";
  retry.addEventListener("click", () => location.reload());
  section.append(heading, message, retry);
  view.replaceChildren(section);
}
