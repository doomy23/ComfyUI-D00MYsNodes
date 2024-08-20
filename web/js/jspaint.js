import { app } from "../../../scripts/app.js";
import { $el } from "../../../scripts/ui.js";

app.registerExtension({
	name: "D00MYs.JSPaint",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "JSPaint|D00MYs") {
            console.log("====================== INIT OF JSPAINT"); 

            function init(value) {
                console.log(value);
                console.log(this);
                console.log(nodeData);
                console.log(app);

                var div = $el("div", {
                    parent: this.content,
                    innerHTML: "<iframe src=\"jspaint/index.html\" id=\"jspaint-iframe-"+nodeData.id+"\" width=\"100%\" height=\"100%\"></iframe>",
                    style: {
                        maxHeight: "600px",
                        overflow: "auto",
                    },
                });
                this.addDOMWidget("JSPAINT", "iframe", div, {});
            }

            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function () {
                onConfigure?.apply(this, arguments);
                if (this.widgets_values?.length) {
                    init.call(this, this.widgets_values[0]);
                } else {
                    init.call(this, null);
                }
            };
        }
    }
});