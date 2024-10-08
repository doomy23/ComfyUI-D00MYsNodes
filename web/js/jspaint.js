import { app } from "../../../scripts/app.js";
import { $el } from "../../../scripts/ui.js";

// JSPAINT Instances
let JSPAINT_INSTANCES = {};

// Node functions
function uuid() {
    return crypto.randomUUID();
}

function findWidget(node, value, attr = "name", func = "find") {
    return node?.widgets ? node.widgets[func]((w) => w[attr] === value) : null;
}

function get_position_style(ctx, widget_width, y, node_height) {
    const MARGIN = 20;
    const elRect = ctx.canvas.getBoundingClientRect();
    const transform = new DOMMatrix()
        .scaleSelf(elRect.width / ctx.canvas.width, elRect.height / ctx.canvas.height)
        .multiplySelf(ctx.getTransform())
        .translateSelf(MARGIN, MARGIN + y);

    return {
        transformOrigin: '0 0',
        transform: transform,
        left: `0px`, 
        top: `0px`,
        position: "absolute",
        width: `${widget_width - MARGIN*2}px`,
        height: `${node_height - MARGIN*2}px`,
    }
}

function JSPAINT() {
    // Create widget
    const uid  = uuid();
    const div = $el("div", {
        innerHTML: "<iframe src=\"jspaint/index.html\" id=\""+uid+"\" width=\"100%\" height=\"100%\"></iframe>",
        style: {
            overflow: "auto",
        },
    });
    const widget = {
        uid,
        type: "JSPAINT",
        name: "image",
        options: {
            forceInput: false,
        },
        inputEl: div,
        value: null,
        computeSize: () => { return [500, 425]; },
        onRemove: () => { 
            delete JSPAINT_INSTANCES[uid];
        },
        draw(ctx, node, width, y) {
            Object.assign(this.inputEl.style, get_position_style(ctx, width, y, node.size[1]));
        },
        async serializeValue(node, widgetIndex) {
            const widget = findWidget(node, "JSPAINT", "type");
            const iframe = document.getElementById(widget.uid);
            const jspaint = iframe.contentWindow;
            const hash = jspaint.location.hash.split(":")[jspaint.location.hash.split(":").length - 1];
            const imageKey = `image#${hash}`
            return jspaint.localStorage.getItem(imageKey);
        }
    };
    return widget;
}

app.registerExtension({
	name: "D00MYs.JSPaint",
    getCustomWidgets(app) {
        return {
          JSPAINT: (node, inputName, inputData, app) => {
            Object.assign(node, {size: [825, 575]});
            const widget = JSPAINT();
            node.onRemoved = function () {
                for (const w of node?.widgets) {
                  if (w?.inputEl) w.inputEl.remove();
                }
            };
            node.addCustomWidget(widget);
            return widget;
          },
        };
      },
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "JSPaint|D00MYs") {
            // Init
            function created(ret) {
                this.serialize_widgets = true;
                this.name = `${nodeData.name}_${this.id}`;
                const widget = findWidget(this, "JSPAINT", "type");
                document.body.appendChild(widget.inputEl);
                return ret;
            }

            // onNodeCreated
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = async function () {
                const ret = onNodeCreated?.apply(this, arguments);
                return created.call(this, ret);
            };
        }
    }
});