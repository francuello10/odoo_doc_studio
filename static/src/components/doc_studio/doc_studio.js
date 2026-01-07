/* @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { ShareDialog } from "../share_dialog/share_dialog";
import { DocSidebar } from "../doc_sidebar/doc_sidebar";
import { DocContent } from "../doc_content/doc_content";

export class DocStudio extends Component {
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.actionService = useService("action");
        this.state = useState({
            currentDocId: null,
            treeData: [],
            searchResults: [],
            searchTerm: "",
            isLoading: true,
        });

        onWillStart(async () => {
            // Auto-sync files from disk on open
            try {
                await this.orm.call("doc.page", "sync_all_from_disk", []);
            } catch (e) {
                console.warn("Auto-sync failed:", e);
            }
            await this.loadTree();
        });
    }

    // ... (existing methods loadTree, onSearchInput, performSearch, createPage, onPageSelected, onPageUpdated) ...

    async loadTree() {
        this.state.isLoading = true;
        try {
            this.state.treeData = await this.orm.call("doc.page", "get_nav_tree", []);

            // Check for active_id in action context (deep linking)
            let deepLinkId = null;
            if (this.props.action?.context?.active_id) {
                deepLinkId = this.props.action.context.active_id;
            } else if (this.props.action?.params?.active_id) {
                deepLinkId = this.props.action.params.active_id;
            }

            if (deepLinkId) {
                this.state.currentDocId = parseInt(deepLinkId);
            } else if (!this.state.currentDocId && this.state.treeData.length > 0) {
                // Auto-select first page if none selected
                this.state.currentDocId = this.state.treeData[0].id;
            }
        } catch (error) {
            console.error("Error loading doc tree:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async onSearchInput(ev) {
        this.state.searchTerm = ev.target.value;
        if (this.searchTimeout) clearTimeout(this.searchTimeout);

        if (!this.state.searchTerm) {
            this.state.searchResults = [];
            return;
        }

        this.searchTimeout = setTimeout(() => this.performSearch(), 300);
    }

    async performSearch() {
        if (!this.state.searchTerm) return;

        try {
            const domain = [['name', 'ilike', this.state.searchTerm]];
            this.state.searchResults = await this.orm.searchRead("doc.page", domain, ["id", "name", "parent_id"]);
        } catch (error) {
            console.error("Error searching docs:", error);
        }
    }

    async createPage() {
        this.state.isLoading = true;
        try {
            const result = await this.orm.create("doc.page", [{
                name: "New Page",
                content_md: "# New Page\n\nStart writing...",
            }]);
            if (result && result.length > 0) {
                await this.loadTree();
                this.state.currentDocId = result[0];
                this.state.forceEdit = true; // Signal DocContent to enter edit mode
                this.state.searchTerm = ""; // Clear search
                this.state.searchResults = [];
            }
        } catch (error) {
            console.error("Error creating page:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    onPageSelected(docId) {
        this.state.currentDocId = docId;
        this.state.forceEdit = false; // Reset on manual selection
    }

    async onPageUpdated() {
        // Refresh tree in case name changed or hierarchy changed
        await this.loadTree();
        // Re-run search if active
        if (this.state.searchTerm) {
            await this.performSearch();
        }
    }

    openShareDialog() {
        if (!this.state.currentDocId) return;
        this.dialog.add(ShareDialog, {
            docId: this.state.currentDocId,
            docName: "this document",
            close: () => { /* Dialog handles close */ }
        });
    }

    openList() {
        this.actionService.doAction("odoo_doc_studio.action_doc_page_list");
    }
}

DocStudio.template = "odoo_doc_studio.DocStudio";
DocStudio.components = { DocSidebar, DocContent };
DocStudio.props = { "*": true };

registry.category("actions").add("odoo_doc_studio.DocStudio", DocStudio);
