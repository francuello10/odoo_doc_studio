/* @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

export class ShareDialog extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            shares: [],
            visibility: 'internal',
            searchTerm: '',
            searchResults: [],
            loading: true,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            // Read doc visibility
            const [doc] = await this.orm.read("doc.page", [this.props.docId], ["visibility"]);
            this.state.visibility = doc.visibility;

            // Read existing shares
            const shares = await this.orm.searchRead("doc.share",
                [["page_id", "=", this.props.docId]],
                ["user_id", "permission"]
            );
            this.state.shares = shares;
        } catch (error) {
            console.error("Error loading share data:", error);
        } finally {
            this.state.loading = false;
        }
    }

    async onUserSearch(ev) {
        const term = ev.target.value;
        this.state.searchTerm = term;
        if (!term) {
            this.state.searchResults = [];
            return;
        }

        // Simple debounce could be added here
        try {
            const domain = [['name', 'ilike', term], ['share', '=', True]]; // Filter internal users usually
            this.state.searchResults = await this.orm.searchRead("res.users", domain, ["id", "name", "email", "avatar_128"], { limit: 5 });
        } catch (error) {
            console.error("Error searching users:", error);
        }
    }

    async addUser(user) {
        try {
            await this.orm.create("doc.share", [{
                page_id: this.props.docId,
                user_id: user.id,
                permission: 'read',
            }]);
            this.state.searchTerm = '';
            this.state.searchResults = [];
            await this.loadData();
            this.notification.add(`Shared with ${user.name}`, { type: "success" });
        } catch (error) {
            this.notification.add("Could not share document", { type: "danger" });
        }
    }

    async updatePermission(shareId, permission) {
        try {
            await this.orm.write("doc.share", [shareId], { permission });
            await this.loadData();
        } catch (error) {
            this.notification.add("Failed to update permission", { type: "danger" });
        }
    }

    async removeShare(shareId) {
        try {
            await this.orm.unlink("doc.share", [shareId]);
            await this.loadData();
        } catch (error) {
            this.notification.add("Failed to remove access", { type: "danger" });
        }
    }

    async onVisibilityChange(ev) {
        const newVisibility = ev.target.value;
        try {
            await this.orm.write("doc.page", [this.props.docId], { visibility: newVisibility });
            this.state.visibility = newVisibility;
            this.notification.add("Visibility updated", { type: "success" });
        } catch (error) {
            this.notification.add("Failed to update visibility", { type: "danger" });
        }
    }

    async copyLink() {
        // Construct deep link
        const origin = window.location.origin;
        // This assumes standard web client URL structure
        const link = `${origin}/web#action=odoo_doc_studio.action_doc_studio&active_id=${this.props.docId}`;

        try {
            await navigator.clipboard.writeText(link);
            this.notification.add("Link copied to clipboard", { type: "success" });
        } catch (err) {
            this.notification.add("Failed to copy link", { type: "danger" });
        }
    }
}

ShareDialog.template = "odoo_doc_studio.ShareDialog";
ShareDialog.components = { Dialog };
