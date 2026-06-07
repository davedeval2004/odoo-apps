/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { markup } from "@odoo/owl";

export class HelpChatbotSystray extends Component {
    static template = "odoo_help_chatbot.HelpChatbotSystray";
    static props = {};

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            isOpen: false,
            messages: [],
            inputValue: "",
            isLoading: false,
            sessionId: null,
            errorMessage: "",
            // Attachment state
            attachedImage: null,      // data URL for preview
            attachedFileName: "",
            attachedImageData: null,   // raw base64 data URL to send to backend
            // Full image preview
            previewImageSrc: null,
        });
        this.messagesContainer = useRef("messagesContainer");
        this.inputField = useRef("inputField");
        this.fileInput = useRef("fileInput");
        this.rootRef = useRef("root");

        this._onClickOutside = this._onClickOutside.bind(this);
        onMounted(() => {
            document.addEventListener("mousedown", this._onClickOutside);
        });
        onWillUnmount(() => {
            document.removeEventListener("mousedown", this._onClickOutside);
        });
    }

    _onClickOutside(ev) {
        if (this.state.isOpen && this.rootRef.el && !this.rootRef.el.contains(ev.target)) {
            // Don't close if image preview is open
            if (this.state.previewImageSrc) {
                return;
            }
            this.state.isOpen = false;
        }
    }

    get suggestions() {
        return [
            { label: "Can't confirm sales order", text: "I cannot confirm my sales order" },
            { label: "Invoice not posting", text: "Invoice is not posting" },
            { label: "Create purchase order", text: "How to create a purchase order?" },
        ];
    }

    togglePanel() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            this.state.errorMessage = "";
            if (this.state.messages.length === 0 && !this.state.sessionId) {
                this._loadHistory();
            }
            setTimeout(() => {
                if (this.inputField.el) {
                    this.inputField.el.focus();
                }
            }, 100);
        }
    }

    async _loadHistory() {
        try {
            const result = await rpc("/help_chatbot/history", {
                session_id: this.state.sessionId,
            });
            if (result.messages && result.messages.length > 0) {
                this.state.messages = result.messages;
                this.state.sessionId = result.session_id;
                this._scrollToBottom();
            }
        } catch (e) {
            // Silently fail
        }
    }

    // ── Attachment handling ──────────────────────────────────────────

    triggerFileInput() {
        if (this.fileInput.el) {
            this.fileInput.el.value = "";
            this.fileInput.el.click();
        }
    }

    onFileSelected(ev) {
        const file = ev.target.files && ev.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith("image/")) {
            this.notification.add("Please select an image file (PNG, JPG, GIF, WebP).", {
                type: "warning",
            });
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.notification.add("Image is too large. Maximum size is 10 MB.", {
                type: "warning",
            });
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.state.attachedImage = e.target.result;
            this.state.attachedImageData = e.target.result;
            this.state.attachedFileName = file.name;
        };
        reader.readAsDataURL(file);
    }

    removeAttachment() {
        this.state.attachedImage = null;
        this.state.attachedImageData = null;
        this.state.attachedFileName = "";
        if (this.fileInput.el) {
            this.fileInput.el.value = "";
        }
    }

    previewImage(src) {
        this.state.previewImageSrc = src;
    }

    closePreview() {
        this.state.previewImageSrc = null;
    }

    // ── Input handling ──────────────────────────────────────────────

    onInputKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    onInputChange(ev) {
        this.state.inputValue = ev.target.value;
        ev.target.style.height = "auto";
        ev.target.style.height = Math.min(ev.target.scrollHeight, 100) + "px";
    }

    sendSuggestion(text) {
        this.state.inputValue = text;
        this.sendMessage();
    }

    // ── Send message ────────────────────────────────────────────────

    async sendMessage() {
        const question = this.state.inputValue.trim();
        const imageData = this.state.attachedImageData;
        const imagePreview = this.state.attachedImage;

        if ((!question && !imageData) || this.state.isLoading) {
            return;
        }

        // Build display content for the message bubble
        const displayContent = question || (imageData ? "" : "");

        // Add user message to UI (with image thumbnail if attached)
        this.state.messages.push({
            role: "user",
            content: displayContent,
            image: imagePreview || null,
        });

        // Clear input and attachment
        this.state.inputValue = "";
        this.state.attachedImage = null;
        this.state.attachedImageData = null;
        this.state.attachedFileName = "";
        this.state.isLoading = true;
        this.state.errorMessage = "";

        if (this.inputField.el) {
            this.inputField.el.style.height = "auto";
        }
        if (this.fileInput.el) {
            this.fileInput.el.value = "";
        }

        this._scrollToBottom();

        try {
            const params = {
                question: question,
                session_id: this.state.sessionId,
            };
            if (imageData) {
                params.image_data = imageData;
            }

            const result = await rpc("/help_chatbot/ask", params);

            if (result.error) {
                this.state.errorMessage = result.message;
            } else {
                this.state.messages.push({
                    role: "assistant",
                    content: result.answer,
                });
                this.state.sessionId = result.session_id;
            }
        } catch (e) {
            this.state.errorMessage =
                "Could not reach the AI service. Please check your connection and try again.";
        } finally {
            this.state.isLoading = false;
            this._scrollToBottom();
            setTimeout(() => {
                if (this.inputField.el) {
                    this.inputField.el.focus();
                }
            }, 50);
        }
    }

    // ── Session management ──────────────────────────────────────────

    async newSession() {
        try {
            const result = await rpc("/help_chatbot/new_session", {});
            this.state.sessionId = result.session_id;
        } catch (e) {
            this.state.sessionId = crypto.randomUUID
                ? crypto.randomUUID()
                : Date.now().toString();
        }
        this.state.messages = [];
        this.state.errorMessage = "";
        this.state.inputValue = "";
        this.removeAttachment();
    }

    async clearHistory() {
        try {
            await rpc("/help_chatbot/clear_history", {
                session_id: this.state.sessionId,
            });
        } catch (e) {
            // Continue
        }
        this.state.messages = [];
        this.state.sessionId = null;
        this.state.errorMessage = "";
        this.state.inputValue = "";
        this.removeAttachment();
    }

    // ── Formatting ──────────────────────────────────────────────────

    formatMessage(content) {
        if (!content) return "";
        let html = content;

        html = html
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/__(.*?)__/g, "<strong>$1</strong>");

        html = html.replace(
            /^(The Issue:|The Fix:|Why This Happens:|Pro Tip:)/gm,
            '<strong class="d-block mt-2 text-primary">$1</strong>'
        );

        html = html.replace(/^-{3,}$/gm, '<hr class="my-2"/>');
        html = html.replace(/^(\d+)\.\s+(.*)$/gm, '<div class="ms-2">$1. $2</div>');

        html = html.replace(
            /([A-Z][a-zA-Z\s]+(?:\s*&gt;\s*[A-Z][a-zA-Z\s]+)+)/g,
            '<code class="text-primary bg-primary-subtle px-1 rounded">$1</code>'
        );

        html = html.replace(/\n/g, "<br/>");
        return markup(html);
    }

    _scrollToBottom() {
        setTimeout(() => {
            const container = this.messagesContainer.el;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }, 50);
    }
}

registry
    .category("systray")
    .add("odoo_help_chatbot.HelpChatbot", { Component: HelpChatbotSystray }, { sequence: 1 });
