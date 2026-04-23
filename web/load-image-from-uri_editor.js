const CSS_ID = "load-image-from-uri-editor-css";


export function openUriEditor(widget, node) {
  ensureUriEditorStyles();

  const overlay = document.createElement("div");
  overlay.className = "load-image-uri-editor-overlay";

  const dialog = document.createElement("div");
  dialog.className = "load-image-uri-editor";

  const label = document.createElement("label");
  label.textContent = "Value";

  const input = document.createElement("textarea");
  input.value = widget.value ?? "";
  input.rows = 1;
  input.spellcheck = false;

  const okButton = document.createElement("button");
  okButton.type = "button";
  okButton.textContent = "OK";

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.textContent = "Cancel";

  const buttonRow = document.createElement("div");
  buttonRow.className = "load-image-uri-editor-buttons";
  buttonRow.append(okButton, cancelButton);
  dialog.append(label, input, buttonRow);
  overlay.append(dialog);
  document.body.append(overlay);

  const close = (save) => {
    if (save) {
      widget.value = input.value;
      node.setDirtyCanvas(true, true);
    }
    overlay.remove();
  };

  okButton.addEventListener("click", () => close(true));
  cancelButton.addEventListener("click", () => close(false));
  overlay.addEventListener("mousedown", (event) => {
    if (event.target === overlay) {
      close(false);
    }
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      close(false);
    } else if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      close(true);
    }
  });

  requestAnimationFrame(() => {
    input.focus();
    input.select();
  });
}


function ensureUriEditorStyles() {
  if (document.getElementById(CSS_ID)) {
    return;
  }

  const link = document.createElement("link");
  link.id = CSS_ID;
  link.rel = "stylesheet";
  link.href = new URL("./load-image-from-uri_editor.css", import.meta.url).href;
  document.head.append(link);
}
