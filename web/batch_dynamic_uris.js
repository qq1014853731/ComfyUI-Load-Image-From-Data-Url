import { app } from "../../scripts/app.js";

const NODE_CLASS = "LoadImageFromURIBatch";
const URI_NAME_PATTERN = /^uri_(\d+)$/;
const CONTROL_WIDGET_NAMES = new Set(["add_uri", "remove_uri"]);

function isUriWidget(widget) {
  return widget?.name && URI_NAME_PATTERN.test(widget.name);
}

function getUriWidgets(node) {
  return (node.widgets || []).filter(isUriWidget);
}

function nextUriIndex(node) {
  let maxIndex = 0;
  // Use a monotonically increasing suffix so removing uri_2 does not rename
  // existing widgets and break serialized workflow values.
  for (const widget of getUriWidgets(node)) {
    const match = widget.name.match(URI_NAME_PATTERN);
    maxIndex = Math.max(maxIndex, Number(match[1]));
  }
  return maxIndex + 1;
}

function moveWidgetBeforeControls(node, widget) {
  const widgets = node.widgets || [];
  const widgetIndex = widgets.indexOf(widget);
  const firstControlIndex = widgets.findIndex((item) => CONTROL_WIDGET_NAMES.has(item.name));
  // Keep URI fields above the add/remove buttons.
  if (widgetIndex === -1 || firstControlIndex === -1 || widgetIndex < firstControlIndex) {
    return;
  }
  widgets.splice(widgetIndex, 1);
  widgets.splice(firstControlIndex, 0, widget);
}

function addUriWidget(node, value = "") {
  // The widget name becomes the backend kwarg name: uri_1, uri_2, ...
  const widget = node.addWidget("text", `uri_${nextUriIndex(node)}`, value, () => {}, {
    multiline: true,
  });
  widget.serialize = true;
  moveWidgetBeforeControls(node, widget);
  resizeNode(node);
  return widget;
}

function removeLastUriWidget(node) {
  const widgets = getUriWidgets(node);
  const widget = widgets[widgets.length - 1];
  if (!widget) {
    return;
  }
  node.widgets.splice(node.widgets.indexOf(widget), 1);
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

  if (!node.widgets?.some((widget) => widget.name === "remove_uri")) {
    const removeButton = node.addWidget("button", "remove_uri", "Remove Last URI", () => {
      removeLastUriWidget(node);
    });
    removeButton.serialize = false;
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
      for (const widget of [...getUriWidgets(this)]) {
        this.widgets.splice(this.widgets.indexOf(widget), 1);
      }
      for (const widget of [...(this.widgets || [])]) {
        if (CONTROL_WIDGET_NAMES.has(widget.name)) {
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
