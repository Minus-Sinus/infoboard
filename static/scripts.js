
function update_infoboard(name_shortname) {
    // alert('Now changing to: ' + sym);
    document.getElementById('q').value = name_shortname;
    // alert('Form filled with dymbol');
    document.change_stock.submit();
    return 0;
};

// Execute when the DOM is fully loaded
$(document).ready(function() {

    configure();
});


// Configure application
function configure() {

    // Configure typeahead
    $("#q").typeahead({
        highlight: false,
        name: 'q',
        minLength: 1,
        hint: true
    }, {
        display: function(suggestion) { return null; },
        limit: 10,

        valueKey: "WKN",
        source: search,
        templates: {
            suggestion: Handlebars.compile("<div style=\"text-align:left;\">{{AssetName}} ({{AssetShortName}} - {{WKN}})</div>")
        }
    });

    // Re-center map after place is selected from drop-down
    $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {
        update_infoboard(suggestion.WKN);

    });

    // Give focus to text box
    $("#q").focus();
}

// Search database for typeahead's suggestions
function search(query, syncResults, asyncResults) {
    // Get places matching query (asynchronously)
    let parameters = {
        q: query
    };
    $.getJSON("/search", parameters, function(data, textStatus, jqXHR) {

        // Call typeahead's callback with search results (i.e. stocks)
        asyncResults(data);
    });
}
