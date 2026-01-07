/* @odoo-module */

import { Component, useState } from "@odoo/owl";

export class DocSidebar extends Component {
    setup() {
        this.state = useState({
            expanded: {}, // Track expanded folders by ID
        });
    }

    toggleExpand(nodeId, event) {
        event.stopPropagation();
        if (this.state.expanded[nodeId]) {
            delete this.state.expanded[nodeId];
        } else {
            this.state.expanded[nodeId] = true;
        }
    }

    selectPage(nodeId, event) {
        event.stopPropagation();
        this.props.onSelect(nodeId);
    }
}

DocSidebar.template = "odoo_doc_studio.DocSidebar";
DocSidebar.components = { DocSidebar };  // Recursive component
DocSidebar.props = {
    treeData: { type: Array },
    currentDocId: { type: Number, optional: true },
    onSelect: { type: Function },
};
