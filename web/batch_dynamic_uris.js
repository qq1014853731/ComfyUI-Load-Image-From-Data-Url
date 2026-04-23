import { app } from "../../scripts/app.js";

const NODE_CLASSES = new Set(["LoadImageFromURIBatch", "LoadImageFromURIList"]);
const URI_NAME_PATTERN = /^uri_(\d+)$/;
const REMOVE_NAME_PATTERN = /^remove_uri_(\d+)$/;
const CONTROL_WIDGET_NAMES = new Set(["add_uri", "remove_uri"]);
const REMOVE_BUTTON_WIDTH = 76;
const REMOVE_BUTTON_GAP = 8;
const ROW_HEIGHT = 32;

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

  // After deleting any item, rename the remaining URI widgets to keep backend
  // kwargs continuous and ordered: uri_1, uri_2, uri_3, ...
  for (const widget of node.widgets || []) {
    if (isUriWidget(widget)) {
      widget.name = `uri_${uriIndex}`;
      uriIndex += 1;
    }
  }
}

function makeUriWidget(node, name, value = "") {
  return {
    name,
    type: "text",
    value,
    serialize: true,

    computeSize(width) {
      return [width, ROW_HEIGHT];
    },

    draw(ctx, nodeArg, width, y, height) {
      const rowHeight = Math.max(ROW_HEIGHT, height || ROW_HEIGHT);
      const leftX = 15;
      const rightX = nodeArg.size[0] - 15;
      const buttonX = rightX - REMOVE_BUTTON_WIDTH;
      const fieldWidth = Math.max(80, buttonX - REMOVE_BUTTON_GAP - leftX);

      ctx.save();

      ctx.strokeStyle = "#777";
      ctx.fillStyle = "#222";
      ctx.lineWidth = 1;
      drawRoundedRect(ctx, leftX, y + 2, fieldWidth, rowHeight - 4, 8);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#aaa";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.font = "14px sans-serif";
      ctx.fillText(this.name, leftX + 10, y + rowHeight / 2);

      ctx.fillStyle = "#eee";
      ctx.textAlign = "right";
      ctx.fillText(shortenValue(ctx, this.value, fieldWidth - 90), leftX + fieldWidth - 10, y + rowHeight / 2);

      ctx.strokeStyle = "#777";
      ctx.fillStyle = "#222";
      drawRoundedRect(ctx, buttonX, y + 2, REMOVE_BUTTON_WIDTH, rowHeight - 4, 8);
      this._removeBounds = { x: buttonX, width: REMOVE_BUTTON_WIDTH };
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#ddd";
      ctx.textAlign = "center";
      ctx.fillText("Remove", buttonX + REMOVE_BUTTON_WIDTH / 2, y + rowHeight / 2);

      ctx.restore();
    },

    mouse(event, pos, nodeArg) {
      if (event.type !== "pointerdown" && event.type !== "mousedown") {
        return false;
      }

      const buttonX = this._removeBounds?.x ?? nodeArg.size[0] - REMOVE_BUTTON_WIDTH - 15;
      const localButtonX = Math.max(0, buttonX - 15);
      const broadButtonX = Math.max(0, nodeArg.size[0] - REMOVE_BUTTON_WIDTH - 40);
      const insideRemoveButton =
        (pos[0] >= buttonX && pos[0] <= buttonX + REMOVE_BUTTON_WIDTH) ||
        (pos[0] >= localButtonX && pos[0] <= localButtonX + REMOVE_BUTTON_WIDTH) ||
        (pos[0] >= broadButtonX && pos[0] <= nodeArg.size[0]);
      if (insideRemoveButton) {
        removeUriWidget(nodeArg, this);
        return true;
      }

      const nextValue = window.prompt(`Edit ${this.name}`, this.value ?? "");
      if (nextValue !== null) {
        this.value = nextValue;
        nodeArg.setDirtyCanvas(true, true);
      }
      return true;
    },
  };
}

function shortenValue(ctx, value, maxWidth) {
  const text = String(value ?? "");
  if (!text || ctx.measureText(text).width <= maxWidth) {
    return text;
  }

  const ellipsis = "...";
  let start = 0;
  let end = text.length;
  while (start < end) {
    const mid = Math.ceil((start + end) / 2);
    const candidate = ellipsis + text.slice(text.length - mid);
    if (ctx.measureText(candidate).width <= maxWidth) {
      start = mid;
    } else {
      end = mid - 1;
    }
  }
  return ellipsis + text.slice(text.length - start);
}

function drawRoundedRect(ctx, x, y, width, height, radius) {
  if (ctx.roundRect) {
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, radius);
    return;
  }

  const right = x + width;
  const bottom = y + height;
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(right - radius, y);
  ctx.quadraticCurveTo(right, y, right, y + radius);
  ctx.lineTo(right, bottom - radius);
  ctx.quadraticCurveTo(right, bottom, right - radius, bottom);
  ctx.lineTo(x + radius, bottom);
  ctx.quadraticCurveTo(x, bottom, x, bottom - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
}

function addUriWidget(node, value = "") {
  // The widget name becomes the backend kwarg name: uri_1, uri_2, ...
  const widget = makeUriWidget(node, `uri_${nextUriIndex(node)}`, value);
  node.addCustomWidget(widget);
  moveWidgetBeforeAddButton(node, widget);
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

  widgets.splice(uriIndex, 1);

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

function extractSerializedUriValues(info, nodeData) {
  const values = info?.widgets_values;
  if (!Array.isArray(values)) {
    return [];
  }

  // Base widgets from Python are serialized first:
  // Batch: timeout, max_download_bytes, size_mode, allow_empty.
  // List: timeout, max_download_bytes, allow_empty.
  // URI widgets are added by this extension after those base widgets.
  const baseWidgetCount = nodeData.name === "LoadImageFromURIBatch" ? 4 : 3;
  return values.slice(baseWidgetCount).filter((value) => typeof value === "string");
}

app.registerExtension({
  name: "ComfyUI.LoadImageFromURI.BatchDynamicURIs",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_CLASSES.has(nodeData.name)) {
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
      const uriValues = extractSerializedUriValues(info, nodeData);
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
