import { app } from "../../scripts/app.js";
import { openUriEditor } from "./load-image-from-uri_editor.js";

const NODE_CLASSES = new Set(["LoadImageFromURIBatch", "LoadImageFromURIList"]);
const URI_NAME_PATTERN = /^uri_(\d+)$/;
const CONTROL_WIDGET_NAMES = new Set(["add_uri"]);
const DEBUG_PREFIX = "[LoadImageFromURI dynamic uris]";

// LiteGraph custom widgets must report a height from computeSize. This matches
// ComfyUI's default widget row height and keeps the custom controls aligned with
// built-in widgets.
const DEFAULT_WIDGET_HEIGHT = 20;

const REMOVE_BUTTON_WIDTH = 104;
const URI_FIELD_MIN_WIDTH = 80;
const URI_ROW_GAP = 6;

const WIDGET_BACKGROUND = "#1f1f1f";
const WIDGET_BORDER = "#666";
const WIDGET_TEXT = "#ddd";
const WIDGET_MUTED_TEXT = "#aaa";

function isUriWidget(widget) {
  return widget?.name && URI_NAME_PATTERN.test(widget.name);
}

function isDynamicWidget(widget) {
  return isUriWidget(widget) || CONTROL_WIDGET_NAMES.has(widget?.name);
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
  if (widgetIndex === -1 || addButtonIndex === -1 || widgetIndex < addButtonIndex) {
    return;
  }

  widgets.splice(widgetIndex, 1);
  widgets.splice(addButtonIndex, 0, widget);
}

function renumberUriWidgets(node) {
  let uriIndex = 1;

  // Keep backend kwargs continuous and ordered: uri_1, uri_2, uri_3, ...
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
    type: "uri_row",
    value,
    serialize: true,
    options: {},

    computeSize(width) {
      return [width, DEFAULT_WIDGET_HEIGHT];
    },

    draw(ctx, nodeArg, width, y, height) {
      const rowHeight = height || DEFAULT_WIDGET_HEIGHT;
      const widgetY = y + 1;
      const widgetHeight = Math.max(1, rowHeight - 2);
      const rightX = nodeArg.size[0] - 15;
      const buttonX = rightX - REMOVE_BUTTON_WIDTH;
      const fieldWidth = Math.max(URI_FIELD_MIN_WIDTH, buttonX - URI_ROW_GAP - 15);

      this._hitAreas = {
        field: {
          nodeX: 15,
          localX: 0,
          width: fieldWidth,
        },
        remove: {
          nodeX: buttonX,
          localX: buttonX - 15,
          width: REMOVE_BUTTON_WIDTH,
        },
      };

      ctx.save();
      ctx.textBaseline = "middle";
      ctx.font = "14px sans-serif";
      ctx.lineWidth = 1;

      ctx.strokeStyle = WIDGET_BORDER;
      ctx.fillStyle = WIDGET_BACKGROUND;
      drawPill(ctx, 15, widgetY, fieldWidth, widgetHeight);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = WIDGET_MUTED_TEXT;
      ctx.textAlign = "left";
      ctx.fillText(this.name, 15 + 10, y + rowHeight / 2);

      ctx.fillStyle = WIDGET_TEXT;
      ctx.textAlign = "right";
      ctx.fillText(
        shortenValue(ctx, this.value, fieldWidth - 92),
        15 + fieldWidth - 10,
        y + rowHeight / 2
      );

      ctx.strokeStyle = WIDGET_BORDER;
      ctx.fillStyle = WIDGET_BACKGROUND;
      drawPill(ctx, buttonX, widgetY, REMOVE_BUTTON_WIDTH, widgetHeight);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = WIDGET_TEXT;
      ctx.textAlign = "center";
      ctx.fillText("Remove", buttonX + REMOVE_BUTTON_WIDTH / 2, y + rowHeight / 2);
      ctx.restore();
    },

    mouse(event, pos, nodeArg) {
      if (event.type !== "pointerdown" && event.type !== "mousedown") {
        return false;
      }

      const localXValues = getPossibleLocalXValues(event, pos, nodeArg);
      const removeHit = isInsideHitArea(localXValues, this._hitAreas?.remove);
      const fieldHit = isInsideHitArea(localXValues, this._hitAreas?.field);

      event.preventDefault?.();
      event.stopPropagation?.();

      if (removeHit) {
        removeUriWidget(nodeArg, this);
        return true;
      }

      if (fieldHit) {
        openUriEditor(this, nodeArg);
      }
      return true;
    },

    onMouseDown(event, pos, nodeArg) {
      return this.mouse(event, pos, nodeArg);
    },

    onClick(event, pos, nodeArg) {
      return this.mouse(event, pos, nodeArg);
    },
  };
}

function makeAddUriWidget(node) {
  return {
    name: "add_uri",
    type: "add_uri_button",
    value: "add_uri",
    serialize: false,
    options: {},

    computeSize(width) {
      return [width, DEFAULT_WIDGET_HEIGHT];
    },

    draw(ctx, nodeArg, width, y, height) {
      const rowHeight = height || DEFAULT_WIDGET_HEIGHT;
      const widgetY = y + 1;
      const widgetHeight = Math.max(1, rowHeight - 2);
      const widgetWidth = Math.max(1, nodeArg.size[0] - 30);

      ctx.save();
      ctx.textBaseline = "middle";
      ctx.font = "14px sans-serif";
      ctx.lineWidth = 1;
      ctx.strokeStyle = WIDGET_BORDER;
      ctx.fillStyle = WIDGET_BACKGROUND;
      drawPill(ctx, FIELD_LEFT, widgetY, widgetWidth, widgetHeight);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = WIDGET_TEXT;
      ctx.textAlign = "center";
      ctx.fillText(this.value, 15 + widgetWidth / 2, y + rowHeight / 2);
      ctx.restore();
    },

    mouse(event, pos, nodeArg) {
      if (event.type !== "pointerdown" && event.type !== "mousedown") {
        return false;
      }

      event.preventDefault?.();
      event.stopPropagation?.();
      addUriWidget(nodeArg);
      return true;
    },

    onMouseDown(event, pos, nodeArg) {
      return this.mouse(event, pos, nodeArg);
    },

    onClick(event, pos, nodeArg) {
      return this.mouse(event, pos, nodeArg);
    },
  };
}

function getPossibleLocalXValues(event, pos, node) {
  const values = [];

  if (Array.isArray(pos) && Number.isFinite(pos[0])) {
    values.push(pos[0]);
    values.push(pos[0] - 15);
  }

  if (Number.isFinite(event?.canvasX)) {
    values.push(event.canvasX - node.pos[0]);
    values.push(event.canvasX - node.pos[0] - 15);
  }

  if (Number.isFinite(event?.clientX) && app.canvas?.canvas) {
    const rect = app.canvas.canvas.getBoundingClientRect();
    const canvasX = (event.clientX - rect.left) / app.canvas.ds.scale - app.canvas.ds.offset[0];
    values.push(canvasX - node.pos[0]);
    values.push(canvasX - node.pos[0] - 15);
  }

  return values;
}

function isInsideHitArea(xValues, hitArea) {
  if (!hitArea) {
    return false;
  }

  for (const x of xValues) {
    if (x >= hitArea.nodeX && x <= hitArea.nodeX + hitArea.width) {
      return true;
    }
    if (x >= hitArea.localX && x <= hitArea.localX + hitArea.width) {
      return true;
    }
  }
  return false;
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

function drawPill(ctx, x, y, width, height) {
  drawRoundedRect(ctx, x, y, width, height, height / 2);
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
    node.addCustomWidget(makeAddUriWidget(node));
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
  // Batch: timeout, max_download_bytes, size_mode, uri_missing.
  // List: timeout, max_download_bytes, uri_missing.
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
      }
      resizeNode(this);
    };
  },
});
