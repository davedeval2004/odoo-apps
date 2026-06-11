/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { ImageField, imageField } from "@web/views/fields/image/image_field";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class CameraDialog extends Component {
    static template = "camera_capture_widget.CameraDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        onCapture: Function,
    };

    setup() {
        this.state = useState({
            streaming: false,
            captured: false,
            capturedImage: null,
            facingMode: "user",
            hasMultipleCameras: false,
            errorMessage: null,
        });
        this.videoRef = useRef("videoElement");
        this.canvasRef = useRef("canvasElement");
        this.stream = null;

        onMounted(() => {
            // Defer until the Dialog's DOM is fully rendered
            setTimeout(() => this._startCamera(), 300);
            this._checkMultipleCameras();
        });

        onWillUnmount(() => {
            this._stopStream();
        });
    }

    async _checkMultipleCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.state.hasMultipleCameras =
                devices.filter((d) => d.kind === "videoinput").length > 1;
        } catch {
            this.state.hasMultipleCameras = false;
        }
    }

    async _startCamera() {
        this.state.errorMessage = null;
        this.state.streaming = false;
        try {
            if (!navigator.mediaDevices?.getUserMedia) {
                this.state.errorMessage = _t(
                    "Camera API is not supported in this browser. Please use a modern browser."
                );
                return;
            }
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: this.state.facingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                },
                audio: false,
            });
            const videoEl = this.videoRef.el;
            if (videoEl) {
                videoEl.srcObject = this.stream;
                videoEl.onloadedmetadata = () => {
                    videoEl.play();
                    this.state.streaming = true;
                };
            }
        } catch (err) {
            if (err.name === "NotAllowedError") {
                this.state.errorMessage = _t(
                    "Camera access was denied. Please allow camera permissions and try again."
                );
            } else if (err.name === "NotFoundError" || err.name === "NotReadableError") {
                this.state.errorMessage = _t("No camera found on this device.");
            } else {
                this.state.errorMessage = _t(
                    "Could not access the camera. Please check your device settings."
                );
            }
        }
    }

    _stopStream() {
        if (this.stream) {
            this.stream.getTracks().forEach((t) => t.stop());
            this.stream = null;
        }
        this.state.streaming = false;
    }

    onCapture() {
        const videoEl = this.videoRef.el;
        const canvasEl = this.canvasRef.el;
        if (!videoEl || !canvasEl || !this.state.streaming) return;

        canvasEl.width = videoEl.videoWidth;
        canvasEl.height = videoEl.videoHeight;
        canvasEl.getContext("2d").drawImage(videoEl, 0, 0);

        // JPEG at 0.92 quality is ~70% smaller than PNG with negligible visual difference
        this.state.capturedImage = canvasEl.toDataURL("image/jpeg", 0.92);
        this.state.captured = true;
        this._stopStream();
    }

    async onRetake() {
        this.state.captured = false;
        this.state.capturedImage = null;
        await this._startCamera();
    }

    async onFlipCamera() {
        this._stopStream();
        this.state.facingMode = this.state.facingMode === "user" ? "environment" : "user";
        this.state.captured = false;
        this.state.capturedImage = null;
        await this._startCamera();
    }

    onConfirm() {
        if (this.state.capturedImage) {
            this.props.onCapture(this.state.capturedImage.split(",")[1]);
        }
        this.props.close();
    }

    onDiscard() {
        this._stopStream();
        this.props.close();
    }
}

export class CameraImageField extends ImageField {
    static template = "camera_capture_widget.CameraImageField";
    static components = { ...ImageField.components, CameraDialog };

    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }

    onCameraClick(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.dialogService.add(CameraDialog, {
            onCapture: (base64Data) => this._setCameraImage(base64Data),
        });
    }

    async _setCameraImage(base64Data) {
        await this.props.record.update({ [this.props.name]: base64Data });
    }
}

export const cameraImageField = {
    ...imageField,
    component: CameraImageField,
    displayName: _t("Camera Image"),
    supportedTypes: ["binary"],
};

registry.category("fields").add("camera", cameraImageField);
