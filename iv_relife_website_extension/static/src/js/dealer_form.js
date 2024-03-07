/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.portalDetails = publicWidget.Widget.extend({
    selector: '.o_portal_dealer_form',
    events: {
        'change select[id="country"]': '_onCountryChange',
    },

    /**
     * @override
     */
    start: function () {
        console.log('o_portal_dealer_form activated');
        console.log();
        var def = this._super.apply(this, arguments);

        this.$state = this.$('select[id="state"]');
        this.$stateOptions = this.$state.filter(':enabled').find('option');
        console.log('state field', this.$state);
        console.log('state options', this.$stateOptions);
        this._adaptAddressForm();

        return def;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _adaptAddressForm: function () {
        var $country = this.$('select[id="country"]');
        var countryID = ($country.val() || 0);
        console.log('country ID is : ', countryID);
        this.$stateOptions.detach();
        var $displayedState = this.$stateOptions.filter('[data-country_id=' + countryID + ']');
        var nb = $displayedState.appendTo(this.$state).show().length;
        this.$state.parent().toggle(nb >= 1);
        if (nb == 0){
            alert('There is no state of the selected Country. State is mandatory here.')
        }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onCountryChange: function () {
        console.log('_onCountryChange is triggered')
        this._adaptAddressForm();
    },
});