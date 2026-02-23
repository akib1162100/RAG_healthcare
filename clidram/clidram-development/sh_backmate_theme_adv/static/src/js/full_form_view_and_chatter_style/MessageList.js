/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { MessageList } from "@mail/components/message_list/message_list";

patch(MessageList.prototype, 'sh_form_view_custom', {

    /**
     * This function is a patch method for the MessageList component in Odoo.
     * It is intended to capture the scroll position of the message list view before a patch operation.
     *
     * @function _willPatch
     * @memberof MessageList.prototype
     * @instance
     *
     * @returns {void}
     */
    _willPatch() {
        const lastRenderedValues = this._lastRenderedValues();
        if (!lastRenderedValues) {
            // TODO ABD: REMOVE (traceback in Knowledge to investigate)
            return;
        }
        const { messageListView } = lastRenderedValues;
        if (!messageListView.exists()) {
            return;
        }
        //     this._willPatchSnapshot = {
        //         scrollHeight: messageListView.getScrollableElement().scrollHeight,
        //         scrollTop: messageListView.getScrollableElement().scrollTop,
        //     };
    }
});