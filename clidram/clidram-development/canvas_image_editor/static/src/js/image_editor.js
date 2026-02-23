/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";

export class ImageEditor extends Component {
    setup() {
        this.canvasRef = useRef("canvas");
        this.recordId = this.props.action.context.record_id;
        const ts = new Date().getTime();
        this.imageUrl = this.props.action.context.image_url + "?t=" + ts;

        this.rpc = useService("rpc");
        this.isDrawing = false;

        onMounted(() => {
            this.initFabric();
        });
    }

    initFabric() {
    const canvasEl = this.canvasRef.el;
    // Always fix canvas resolution to 700x700
    canvasEl.width = 700;
    canvasEl.height = 700;

    this.canvas = new fabric.Canvas(canvasEl, {
        selection: true,
        preserveObjectStacking: true,
    });

    if (this.imageUrl) {
        fabric.Image.fromURL(this.imageUrl, (img) => {
            if (!img) {
                console.error("Failed to load image");
                return;
            }

            // Make base image not selectable
            img.set({ selectable: false });

            // Scale image proportionally to fit 700x700
            const scale = Math.min(700 / img.width, 700 / img.height);
            img.scale(scale);

            // Center image
            img.set({
                left: (700 - img.width * scale) / 2,
                top: (700 - img.height * scale) / 2,
            });

            this.canvas.add(img);
            this.canvas.renderAll();
        }, { crossOrigin: "anonymous" });
    }
}

    selectTool(tool) {
        // Always disable free draw first
        this.canvas.isDrawingMode = false;

        switch (tool) {
            case 'draw':
                this.canvas.isDrawingMode = true;
                this.canvas.freeDrawingBrush.color = this.getSelectedColor();
                this.canvas.freeDrawingBrush.width = 3;
                break;
            case 'text':
                this.addText();
                break;
            case 'rectangle':
                this.addRectangle();
                break;
            case 'highlight':
                this.addHighlight();
                break;
            case 'arrow':
                this.addArrow();
                break;
        }
    }

    handleResize() {
        if (!this.canvas || !this.canvasRef || !this.canvasRef.el) {
            return; // Element not available yet
        }

        const canvasEl = this.canvasRef.el;
        canvasEl.width = canvasEl.offsetWidth;
        canvasEl.height = canvasEl.offsetHeight;

        this.canvas.setDimensions({
            width: canvasEl.offsetWidth,
            height: canvasEl.offsetHeight
        });

        this.canvas.renderAll();
    }


    // --- Tools ---
    addText() {
        const text = new fabric.IText('Sample Text', {
            left: 100,
            top: 100,
            fontSize: 20,
            fill: this.getSelectedColor()
        });
        this.canvas.add(text);
    }

    enableFreeDraw() {
        this.canvas.isDrawingMode = true;
        this.canvas.freeDrawingBrush.color = this.getSelectedColor();
        this.canvas.freeDrawingBrush.width = 3;
    }

    addRectangle() {
        const rect = new fabric.Rect({
            left: 100,
            top: 100,
            width: 100,
            height: 60,
            fill: "rgba(255,0,0,0.2)",
            stroke: this.getSelectedColor(),
            strokeWidth: 2
        });
        this.canvas.add(rect);
    }

    addHighlight() {
        const highlight = new fabric.Rect({
            left: 150,
            top: 150,
            width: 80,
            height: 50,
            fill: "rgba(255,255,0,0.3)",
            selectable: true
        });
        this.canvas.add(highlight);
    }

    getSelectedColor() {
        return document.getElementById('colorPicker').value;
    }

    addArrow(fromX = 200, fromY = 200, toX = 300, toY = 250) {
        const strokeColor = this.getSelectedColor() || 'blue';
        const strokeWidth = 3;

        const dx = toX - fromX;
        const dy = toY - fromY;
        const angle = Math.atan2(dy, dx);
        const length = Math.sqrt(dx*dx + dy*dy);

        const headLength = Math.min(20, length * 0.2);
        const headWidth = headLength * 0.6;

        // Adjust line end to account for arrowhead length
        const adjustedEndX = toX - headLength * Math.cos(angle);
        const adjustedEndY = toY - headLength * Math.sin(angle);

        // Create the line
        const line = new fabric.Line([fromX, fromY, adjustedEndX, adjustedEndY], {
            stroke: strokeColor,
            strokeWidth: strokeWidth,
            strokeLineCap: 'round',
            selectable: false
        });

        const arrowX = toX - (headLength / 2) * Math.cos(angle);
        const arrowY = toY - (headLength / 2) * Math.sin(angle);

        const head = new fabric.Triangle({
            left: arrowX,
            top: arrowY,
            originX: 'center',
            originY: 'center',
            angle: angle * (180 / Math.PI) + 90,
            width: headWidth,
            height: headLength,
            fill: strokeColor,
            selectable: false
        });

        const arrow = new fabric.Group([line, head], {
            selectable: true,
            hasControls: true,
            hasBorders: true,
            lockUniScaling: true,
            lockRotation: false
        });

        this.canvas.add(arrow);
        this.canvas.setActiveObject(arrow);
        this.canvas.requestRenderAll();

        return arrow;
    }

    deleteSelected() {
        const activeObjects = this.canvas.getActiveObjects();
        activeObjects.forEach(obj => this.canvas.remove(obj));
        this.canvas.discardActiveObject();
        this.canvas.requestRenderAll();
    }

    discardChanges() {
        this.env.services.action.doAction({ type: "ir.actions.act_window_close" });
    }

    // --- Save ---
async saveImage() {
    const dataUrl = this.canvas.toDataURL("image/png");
    await this.rpc("/image_editor/save", {
        record_id: this.recordId,
        model: this.props.action.context.model,
        field_name: this.props.action.context.field_name,
        image_data: dataUrl
    });

    this.env.services.action.doAction({ type: "ir.actions.act_window_close" });
    this.env.bus.trigger("reload");
}
}
ImageEditor.template = "canvas_image_editor.ImageEditor";

registry.category("actions").add("image_editor_action", ImageEditor);
