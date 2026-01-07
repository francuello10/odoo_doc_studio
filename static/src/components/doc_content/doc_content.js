/* @odoo-module */

import { Component, useState, onWillUpdateProps, onWillStart, useRef, onMounted, onPatched, markup } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Wysiwyg } from "@html_editor/wysiwyg";
import { MAIN_PLUGINS } from "@html_editor/plugin_sets";
import { browser } from "@web/core/browser/browser";

export class DocContent extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.htmlContentRef = useRef("htmlContent");
        this.editor = null;  // Will hold reference to the Wysiwyg editor

        this.state = useState({
            mode: 'view', // 'view' or 'edit'
            viewMode: 'visual', // 'visual' or 'markdown'
            doc: null,
            isLoading: false,
            editContent: '',
            editTitle: '',
            editParentId: false,
            availableParents: [],
            linkedPages: [],
            breadcrumbs: [],
            readingTime: 0,
            showCodeView: false,
        });

        onWillStart(async () => {
            await this.loadParents();
            await this.loadDoc(this.props.docId);
        });

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.docId !== this.props.docId) {
                await this.loadDoc(nextProps.docId);
            }
        });

        // Set innerHTML after mount and patch to render HTML properly
        onMounted(() => this.updateHtmlContent());
        onPatched(() => this.updateHtmlContent());
    }

    updateHtmlContent() {
        if (this.htmlContentRef.el && this.state.doc && this.state.mode === 'view' && this.state.viewMode === 'visual') {
            this.htmlContentRef.el.innerHTML = this.state.doc.body_html || '';
        }
    }

    async loadParents() {
        try {
            this.state.availableParents = await this.orm.searchRead("doc.page", [], ["id", "name"]);
        } catch (error) {
            console.error("Error loading parents:", error);
        }
    }

    async loadDoc(docId) {
        if (!docId) {
            this.state.doc = null;
            return;
        }
        this.state.isLoading = true;
        this.state.mode = 'view';
        try {
            // Smart Sync: Ensure DB is consistent with Disk before reading
            await this.orm.call("doc.page", "action_sync_from_disk", [docId]);

            const result = await this.orm.read("doc.page", [docId], [
                "name", "body_html", "content_md", "parent_id", "linked_page_ids",
                "create_uid", "create_date", "write_uid", "write_date",
                "cover_image", "icon", "locked_by"
            ]);
            if (result && result.length > 0) {
                this.state.doc = result[0];

                // Fetch Breadcrumbs
                this.state.breadcrumbs = await this.orm.call("doc.page", "get_breadcrumbs", [docId]);

                // Calculate Reading Time (avg 200 words per minute)
                const words = (this.state.doc.content_md || "").split(/\s+/).length;
                this.state.readingTime = Math.max(1, Math.ceil(words / 200));

                // Handle body_html - it might be a Markup object or string
                let bodyHtml = this.state.doc.body_html;
                if (bodyHtml && typeof bodyHtml === 'object') {
                    // Odoo Markup object - try to get the actual HTML string
                    if (bodyHtml.__html) {
                        bodyHtml = bodyHtml.__html;
                    } else if (bodyHtml.toString && bodyHtml.toString() !== '[object Object]') {
                        bodyHtml = bodyHtml.toString();
                    } else {
                        bodyHtml = '';
                    }
                }

                // CLEANUP: Ensure we only have a fragment for the visual editor
                bodyHtml = this._cleanHtmlFragment(bodyHtml || '');
                this.state.doc.body_html = bodyHtml;

                // Sync title/parent for edit mode
                this.state.editTitle = this.state.doc.name;
                this.state.editParentId = this.state.doc.parent_id ? String(this.state.doc.parent_id[0]) : '';

                // Load linked page details (names)
                if (this.state.doc.linked_page_ids && this.state.doc.linked_page_ids.length > 0) {
                    const linkedPages = await this.orm.read(
                        "doc.page",
                        this.state.doc.linked_page_ids,
                        ["id", "name"]
                    );
                    this.state.linkedPages = linkedPages;
                } else {
                    this.state.linkedPages = [];
                }

                // Auto-enter edit mode if requested (e.g. from New Page action)
                if (this.props.forceEdit) {
                    this.toggleEdit();
                }
            }
        } catch (error) {
            // Only show error if we are still on the same doc (avoids deletion race conditions)
            if (this.state.doc && this.state.doc.id === docId) {
                console.error("Error loading doc:", error);
                this.notification.add("Failed to load document", { type: "danger" });
            }
        } finally {
            this.state.isLoading = false;
        }
    }

    _cleanHtmlFragment(htmlStr) {
        if (!htmlStr) return '';

        // If it's a full document, extract only the body content
        if (htmlStr.toLowerCase().includes('<html') || htmlStr.toLowerCase().includes('<body')) {
            const bodyMatch = htmlStr.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
            if (bodyMatch && bodyMatch[1]) {
                htmlStr = bodyMatch[1].trim();
            } else {
                // Secondary check: remove technical tags if no body found
                htmlStr = htmlStr.replace(/<!DOCTYPE[^>]*>/i, '')
                    .replace(/<html[^>]*>/i, '')
                    .replace(/<\/html>/i, '')
                    .replace(/<head[^>]*>[\s\S]*?<\/head>/i, '')
                    .replace(/<meta[^>]*>/gi, '')
                    .replace(/<title[^>]*>[\s\S]*?<\/title>/i, '')
                    .replace(/<link[^>]*>/gi, '');
            }
        }
        return htmlStr.trim();
    }

    async toggleViewMode() {
        const newMode = this.state.viewMode === 'visual' ? 'markdown' : 'visual';

        // If in Edit Mode, sync content before switching
        if (this.state.mode === 'edit') {
            this.state.isLoading = true;
            try {
                if (newMode === 'markdown') {
                    // Moving from Visual -> Markdown: Convert latest editor HTML to MD
                    const currentHtml = this.editor ? this.editor.getContent() : this.state.editContent;
                    const mdResult = await this.orm.call("doc.page", "action_convert_html_to_md", [currentHtml]);
                    this.state.editMarkdown = mdResult;
                    this.state.editContent = currentHtml; // Backup current HTML
                } else {
                    // Moving from Markdown -> Visual: Convert current MD string to HTML
                    const htmlResult = await this.orm.call("doc.page", "action_convert_md_to_html", [this.state.editMarkdown]);
                    this.state.editContent = htmlResult;
                }
            } catch (error) {
                console.error("Sync error:", error);
                this.notification.add("Failed to sync content between modes", { type: "warning" });
            } finally {
                this.state.isLoading = false;
            }
        }

        this.state.viewMode = newMode;
    }

    onMarkdownChange(ev) {
        this.state.editMarkdown = ev.target.value;
    }


    async toggleEdit() {
        if (this.state.mode === 'view') {
            // Check Lock
            const lockResult = await this.orm.call("doc.page", "action_acquire_lock", [this.state.doc.id]);
            if (!lockResult.success) {
                this.notification.add(`Document is locked by ${lockResult.locked_by}`, { type: "danger" });
                return;
            }

            // CRITICAL: Ensure editContent is a fresh string from doc.body_html
            this.state.editContent = this.state.doc.body_html || '';
            this.state.editMarkdown = this.state.doc.content_md || '';
            this.state.mode = 'edit';
            this.state.showCodeView = false;
            // Refresh parents list when entering edit mode to ensure it's up to date
            this.loadParents();
        } else {
            // Cancel Edit - Release Lock
            await this.orm.call("doc.page", "action_release_lock", [this.state.doc.id]);

            this.state.mode = 'view';
            this.state.showCodeView = false; // Reset code view when canceling
            // Update HTML content when canceling edit
            this.updateHtmlContent();
        }
    }

    toggleCodeView() {
        if (this.state.showCodeView) {
            // Switching back to Wysiwyg
            this.state.showCodeView = false;
        } else {
            // Switching to Code View
            // Ensure we have the latest content from Wysiwyg before switching
            if (this.editor && typeof this.editor.getContent === 'function') {
                this.state.editContent = this.editor.getContent();
            }
            this.editor = null; // Clear editor reference so save() uses state.editContent
            this.state.showCodeView = true;
        }
    }

    async deletePage() {
        if (!this.state.doc) return;

        this.dialog.add(ConfirmationDialog, {
            title: "Delete Page",
            body: `Are you sure you want to delete "${this.state.doc.name}"? This action cannot be undone.`,
            confirm: async () => {
                const docId = this.state.doc.id;
                try {
                    // Clear state BEFORE unlink to prevent redundant load attempts
                    this.state.doc = null;
                    await this.orm.unlink("doc.page", [docId]);
                    this.notification.add("Document deleted", { type: "success" });
                    this.props.onUpdate();
                } catch (error) {
                    console.error("Error deleting doc:", error);
                    this.notification.add("Failed to delete document", { type: "danger" });
                }
            },
            cancel: () => { },
            confirmLabel: "Delete",
            cancelLabel: "Cancel",
        });
    }

    async save() {
        this.state.isLoading = true;
        try {
            let contentToSave = '';

            // If we are currently in Markdown mode, we need to sync back to HTML before saving
            if (this.state.mode === 'edit' && this.state.viewMode === 'markdown') {
                contentToSave = await this.orm.call("doc.page", "action_convert_md_to_html", [this.state.editMarkdown]);
                this.state.editContent = contentToSave;
            } else {
                // Get content directly from the editor
                if (this.editor && typeof this.editor.getContent === 'function') {
                    contentToSave = this.editor.getContent();
                } else {
                    contentToSave = this.state.editContent || '';
                }
            }

            // Ensure it's a string
            if (typeof contentToSave !== 'string') {
                contentToSave = String(contentToSave || '');
            }

            await this.orm.write("doc.page", [this.state.doc.id], {
                name: this.state.editTitle,
                body_html: contentToSave,  // Write HTML, backend converts to MD
                parent_id: this.state.editParentId ? parseInt(this.state.editParentId) : false,
            });

            // Release Lock
            await this.orm.call("doc.page", "action_release_lock", [this.state.doc.id]);

            // Sync to disk immediately to persist changes to MD files
            await this.orm.call("doc.page", "action_sync_to_disk", [this.state.doc.id]);

            // Reload doc
            await this.loadDoc(this.state.doc.id);

            this.state.mode = 'view';
            this.notification.add("Document saved successfully", { type: "success" });
            this.props.onUpdate();
        } catch (error) {
            console.error("Error saving doc:", error);
            this.notification.add("Failed to save document", { type: "danger" });
        } finally {
            this.state.isLoading = false;
        }
    }

    async updateIcon() {
        // Simple prompt for now, could be an emoji picker later
        const icon = prompt("Enter an emoji for page icon:", this.state.doc.icon || "📄");
        if (icon) {
            await this.orm.write("doc.page", [this.state.doc.id], { icon: icon });
            await this.loadDoc(this.state.doc.id);
        }
    }

    async syncFromDisk() {
        if (!this.state.doc) return;
        this.state.isLoading = true;
        try {
            const hasSynced = await this.orm.call("doc.page", "action_sync_from_disk", [this.state.doc.id]);
            if (hasSynced) {
                this.notification.add("Updated from disk", { type: "success" });
                await this.loadDoc(this.state.doc.id);
            } else {
                this.notification.add("Could not read file from disk", { type: "warning" });
            }
        } catch (error) {
            console.error(error);
            this.notification.add("Sync failed", { type: "danger" });
        } finally {
            this.state.isLoading = false;
        }
    }

    navigateToPage(pageId, ev) {
        ev.preventDefault();
        window.location.hash = `action=odoo_doc_studio.action_doc_studio&active_id=${pageId}`;
        window.location.reload();
    }


    async copyMarkdownToClipboard() {
        if (!this.state.doc || !this.state.doc.content_md) return;
        try {
            await browser.navigator.clipboard.writeText(this.state.doc.content_md);
            this.notification.add("Markdown copied to clipboard!", { type: "success" });
        } catch (err) {
            console.error("Failed to copy", err);
            this.notification.add("Failed to copy to clipboard", { type: "danger" });
        }
    }

    onWysiwygChange(content) {
        // Wysiwyg sometimes calls onChange with internal state objects like {isPreviewing: undefined}
        // We need to filter these out and only process actual HTML content
        if (typeof content === 'object') {
            // Check if it's an internal state update (has isPreviewing property)
            if (content && 'isPreviewing' in content) {
                // Ignore internal state updates
                return;
            }

            // If it's a different kind of object, try to extract HTML
            console.warn('Wysiwyg returned unexpected object:', content);
            if (content && content.outerHTML) {
                this.state.editContent = content.outerHTML;
            } else if (content && content.innerHTML) {
                this.state.editContent = content.innerHTML;
            } else {
                this.state.editContent = String(content);
            }
        } else {
            // Normal case: content is a string
            this.state.editContent = content || '';
        }
    }

    onEditorLoad(editor) {
        this.editor = editor;
    }

    get wysiwygConfig() {
        return {
            content: markup(this.state.editContent || '<p><br></p>'),
            onChange: (content) => {
                // In Odoo 19, content might be a Markup object
                if (content && typeof content === 'object' && content.__html) {
                    this.state.editContent = content.__html;
                } else if (typeof content === 'string') {
                    this.state.editContent = content;
                }
            },
            Plugins: MAIN_PLUGINS,
            baseContainers: ["DIV", "P"],
            powerbox: true,
            resizable: true,
            allowCommandLink: true,
            getRecordInfo: () => {
                return {
                    resModel: 'doc.page',
                    resId: this.state.doc ? this.state.doc.id : null,
                };
            },
        };
    }

    get printUrl() {
        if (!this.state.doc) return '#';
        return `/report/pdf/odoo_doc_studio.report_doc_page_template/${this.state.doc.id}`;
    }
}

DocContent.template = "odoo_doc_studio.DocContent";
DocContent.components = { Wysiwyg };
DocContent.props = {
    docId: { type: Number },
    forceEdit: { type: Boolean, optional: true },
    onUpdate: { type: Function },
};
