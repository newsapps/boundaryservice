var geolocate_supported = true; // until prove false

var geocoder = new google.maps.Geocoder();
var map = null;

var user_marker = null;
var displayed_slug = null;
var displayed_polygon = null;

var boundaries = new Array();

function init_map(lat, lng) {
    if (map == null) {
        var ll = new google.maps.LatLng(lat, lng);

        var map_options = {
            zoom: 14,
            center: ll,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };

        map = new google.maps.Map(document.getElementById("map_canvas"), map_options);
    }

    var center = new google.maps.LatLng(lat, lng);
    map.panTo(center);

    resize_listener(center);
}

function show_user_marker(lat, lng) {
    if (user_marker == null) {
        user_marker = new google.maps.Marker();

        user_marker.setDraggable(true);
        user_marker.setMap(map);

        google.maps.event.addListener(user_marker, 'dragend', function() {
            ll = user_marker.getPosition();
            geocode(new google.maps.LatLng(ll.lat(), ll.lng()))
        });
    }

    user_marker.setPosition(new google.maps.LatLng(lat, lng));
}

function geocode(query) {
    if (typeof(query) == 'string') {
        pattr = /\sil\s|\sillinois\s/gi;
        match = query.match(pattr);
        if (!match) {
            query = query + ' IL';
        }
        gr = { 'address': query };
    } else {
        gr = { 'location': query };
    }
    geocoder.geocode(gr, handle_geocode);
}

function handle_geocode(results, status) {
    lat = results[0].geometry.location.lat();
    lng = results[0].geometry.location.lng();

    normalized_address = results[0].formatted_address;
    $('#location-form #address').val(normalized_address);
    
    process_location(lat, lng);
}

function geolocate() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(geolocation_success, geolocation_error);
    } else {
        process_location(41.890498, -87.62361);

        $('#resultinfo').html('Your browser does not support automatically determining your location so we\'re showing you where <a href="http://twitter.com/#!/coloneltribune">@ColonelTribune</a> lives.');

        geolocate_supported = false;
    }
}

function geolocation_success(position) {
    process_location(position.coords.latitude, position.coords.longitude)

    geocode(new google.maps.LatLng(position.coords.latitude, position.coords.longitude))
    hide_search()
}

function geolocation_error() {
    process_location(41.890498, -87.62361);

    $('#resultinfo').html('We could not automatically determine your location so we\'re showing you where <a href="http://twitter.com/#!/coloneltribune">@ColonelTribune</a> lives.');
}

function process_location(lat, lng) {
    $('#resultinfo').html(
        'Latitude: ' + lat + '<br />' +
        'Longitude: ' + lng + '<br />'
    );

    init_map(lat, lng);
    show_user_marker(lat, lng);
    get_boundaries(lat, lng);
}

// Use boundary service to lookup what areas the location falls within
function get_boundaries(lat, lng) {
    var table_html = '<h3>This location is within:</h3><table id="boundaries" border="0" cellpadding="0" cellspacing="0">';
    var query_url = 'http://{{ domain }}/api/1.0/boundary/?format=jsonp&limit=100&contains='+lat+','+lng+'&callback=?';

    displayed_kind = null;
    for_display = null;

    if (displayed_polygon != null) {
        // Hide old polygon
        displayed_kind = boundaries[displayed_slug].kind;
        displayed_polygon.setMap(null);
        displayed_polygon = null;
        displayed_slug = null;
    }

    // Clear old boundaries
    boundaries.length = 0;

    $.getJSON(query_url, function(data) {
        $.each(data.objects, function(i, obj) {
            boundaries[obj.slug] = obj;
            table_html += '<tr id="' + obj.slug + '"><td>' + obj.kind + '</td><td><strong><a href="javascript:display_boundary(\'' + obj.slug + '\');">' + obj.name + '</a></strong></td></td>';

            // Try to display a new polygon of the same kind as the last shown
            if (displayed_kind != null && obj.kind == displayed_kind) {
                for_display = obj; 
            }
        });
        table_html += '</table>';
        $('#area-lookup').html(table_html);

        if (for_display != null) {
            display_boundary(for_display.slug, true);
        }
    });
}

function display_boundary(slug, no_fit) {
    // Clear old polygons
    if (displayed_polygon != null) {
        displayed_polygon.setMap(null);
        displayed_polygon = null;
        displayed_slug = null;

        $("#boundaries .selected").removeClass("selected");
    }

    // Construct new polygons
    var coords = boundaries[slug]["simple_shape"].coordinates;
    var paths = [];
    var bounds = new google.maps.LatLngBounds(); 

    $.each(coords, function(i, n){
        $.each(n, function(j, o){
            var path = [];

            $.each(o, function(k,p){
                var ll = new google.maps.LatLng(p[1], p[0]);
                path.push(ll);
                bounds.extend(ll);
            });

            paths.push(path);
        });
    });

    displayed_polygon = new google.maps.Polygon({
        paths: paths,
        strokeColor: "#244f79",
        strokeOpacity: 0.8,
        strokeWeight: 3,
        fillColor: "#244f79",
        fillOpacity: 0.2
    });

    displayed_slug = slug;
    displayed_polygon.setMap(map);

    $("#boundaries #" + slug).addClass("selected");

    if (!no_fit) {
        map.fitBounds(bounds);
    }
}

function show_search() {
    $('#not-where-i-am').hide();
    if (geolocate_supported) { $('#use-current-location').fadeIn(); }
    $('#location-form').slideDown();
}

function hide_search() {
    $('#not-where-i-am').show();
    $('#use-current-location').hide()
    $('#location-form').slideUp();
}

function switch_page(page_id) {
    $(".page-content").hide()
    $("#" + page_id + "-page").show()
    window.location.hash = page_id
}

/* DOM EVENT HANDLERS */
function resize_listener(center) {
    $(this).bind('resize_end', function(){ 
        map.panTo(center); 
    });
}

function resize_end_trigger() {
    $(window).resize(function() {
        if (this.resizeto) { 
            clearTimeout(this.resizeto) 
            };

        this.resizeto = setTimeout(function() { 
            $(this).trigger('resize_end'); 
            }, 500);
    });
}

function not_where_i_am() {
    show_search();
}

function use_current_location() {
    geolocate();
}

function search_focused() {
    if(this.value == '{{ default_search_text }}') {
        $(this).val("");
    }
}

function address_search() {
    geocode($("#location-form #address").val());

    return false;
}

$(document).ready(function() {
    // Setup handlers
    $('#not-where-i-am').click(not_where_i_am);
    $('#use-current-location').click(use_current_location);
    $('#location-form input[type=text]').focus(search_focused);
    $('#location-form').submit(address_search)
    
    resize_end_trigger();
    
    if (window.location.hash != "") {
        switch_page(window.location.hash.substring(1));
    } else {
        switch_page("demo");
    }
    
    geolocate();
});

