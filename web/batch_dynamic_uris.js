import { app } from "../../scripts/app.js";

const NODE_CLASS = "LoadImageFromURIBatch";
const URI_NAME_PATTERN = /^uri_(\d+)$/;
const REMOVE_NAME_PATTERN = /^remove_uri_(\d+)$/;
const CONTROL_WIDGET_NAMES = new Set(["add_uri", "remove_uri"]);

function isUriWidget(widget) {
  return widget?.name && URI_NAME_PATTERN.test(widget.name);
}

function isRemoveWidget(widget) {
  return widget?.name && REMOVE_NAME_PATTERN.test(widget.name);
}

function isDynamicWidget(widget) {
  return isUriWidget(widget) || isRemoveWidget(widget) || CONTROL_WIDGET_NAMES.has(widget?.name);
}

function getUriWidgets(node) {
  return (node.widgets || []).filter(isUriWidget);
}

function nextUriIndex(node) {
  return getUriWidgets(node).length + 1;
}

function moveWidgetBeforeAddButton(node, widget) {
  const widgets = node.widgets || [];
  const widgetIndex = widgets.indexOf(widget);
  const addButtonIndex = widgets.findIndex((item) => item.name === "add_uri");
  // Keep URI rows above the add button.
  if (widgetIndex === -1 || addButtonIndex === -1 || widgetIndex < addButtonIndex) {
    return;
  }
  widgets.splice(widgetIndex, 1);
  widgets.splice(addButtonIndex, 0, widget);
}

function renumberUriWidgets(node) {
  let uriIndex = 1;
  let lastUriIndex = null;

  // URI and remove widgets are interleaved: uri_1, remove_uri_1, uri_2, ...
  // After deleting any item, rename the remaining pairs to keep backend kwargs
  // continuous and ordered.
  for (const widget of node.widgets || []) {
    if (isUriWidget(widget)) {
      widget.name = `uri_${uriIndex}`;
      lastUriIndex = uriIndex;
      uriIndex += 1;
    } else if (isRemoveWidget(widget) && lastUriIndex !== null) {
      widget.name = `remove_uri_${lastUriIndex}`;
    }
  }
}

function addUriWidget(node, value = "") {
  // The widget name becomes the backend kwarg name: uri_1, uri_2, ...
  const widget = node.addWidget("text", `uri_${nextUriIndex(node)}`, value, () => {}, {
    multiline: true,
  });
  widget.serialize = true;
  moveWidgetBeforeAddButton(node, widget);

  const removeButton = node.addWidget("button", `remove_${widget.name}`, "Remove", () => {
    removeUriWidget(node, widget);
  });
  removeButton.serialize = false;
  moveWidgetBeforeAddButton(node, removeButton);
  renumberUriWidgets(node);
  resizeNode(node);
  return widget;
}

function removeUriWidget(node, uriWidget) {
  const widgets = node.widgets || [];
  const uriIndex = widgets.indexOf(uriWidget);
  if (uriIndex === -1) {
    return;
  }

  const removeButton = widgets[uriIndex + 1];
  if (isRemoveWidget(removeButton)) {
    widgets.splice(uriIndex, 2);
  } else {
    widgets.splice(uriIndex, 1);
  }

  renumberUriWidgets(node);
  ensureDefaultUriWidget(node);
  resizeNode(node);
}

function resizeNode(node) {
  const computed = node.computeSize();
  node.size[0] = Math.max(node.size[0], computed[0]);
  node.size[1] = computed[1];
  node.setDirtyCanvas(true, true);
}

function ensureControls(node) {
  if (!node.widgets?.some((widget) => widget.name === "add_uri")) {
    const addButton = node.addWidget("button", "add_uri", "+ Add URI", () => addUriWidget(node));
    addButton.serialize = false;
  }
}

function ensureDefaultUriWidget(node) {
  if (!getUriWidgets(node).length) {
    addUriWidget(node);
  }
}

function extractSerializedUriValues(info) {
  const values = info?.widgets_values;
  if (!Array.isArray(values)) {
    return [];
  }

  // Base widgets from Python are serialized first:
  // timeout, max_download_bytes, allow_empty.
  // URI widgets are added by this extension after those base widgets.
  return values.slice(3).filter((value) => typeof value === "string");
}

app.registerExtension({
  name: "ComfyUI.LoadImageFromURI.BatchDynamicURIs",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE_CLASS) {
      return;
    }

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      originalOnNodeCreated?.apply(this, arguments);
      this.serialize_widgets = true;
      ensureControls(this);
      ensureDefaultUriWidget(this);
      resizeNode(this);
    };

    const originalConfigure = nodeType.prototype.configure;
    nodeType.prototype.configure = function (info) {
      const uriValues = extractSerializedUriValues(info);
      originalConfigure?.apply(this, arguments);
      this.serialize_widgets = true;

      // Rebuild dynamic widgets after ComfyUI restores Python-defined widgets.
      for (const widget of [...(this.widgets || [])]) {
        if (isDynamicWidget(widget)) {
          this.widgets.splice(this.widgets.indexOf(widget), 1);
        }
      }

      ensureControls(this);
      if (uriValues.length) {
        for (const value of uriValues) {
          addUriWidget(this, value);
        }
      } else {
        ensureDefaultUriWidget(this);
      }
      resizeNode(this);
    };
  },
});
