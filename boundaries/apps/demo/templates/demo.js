// Geocoder stuff
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

    map.panTo(new google.maps.LatLng(lat, lng));
}

function show_user_marker(lat, lng) {
    if (user_marker == null) {
        user_marker = new google.maps.Marker();

        user_marker.setDraggable(true);
        user_marker.setMap(map);

        google.maps.event.addListener(user_marker, 'dragend', function() {
            ll = user_marker.getPosition();
            process_location(ll.lat(), ll.lng());
        });
    }

    user_marker.setPosition(new google.maps.LatLng(lat, lng));
}

function geocode(address) {
    gr = { 'address': address };
    geocoder.geocode(gr, handle_geocode);
}

function handle_geocode(results, status) {
    lat = results[0].geometry.location.lat();
    lng = results[0].geometry.location.lng();
    
    process_location(lat, lng);
}

function geolocation_success(position) {
    process_location(position.coords.latitude, position.coords.longitude)
}

function geolocation_error() {
    $('#resultinfo').html('The page could not get your location.');
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
    var table_html = '<h3>Your location falls within:</h3><table id="boundaries" border="0" cellpadding="0" cellspacing="0">';
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

    // TODO: clear old boundaries?

    $.getJSON(query_url, function(data) {
        $.each(data.objects, function(i, obj) {
            boundaries[obj.slug] = obj;
            table_html += '<tr><td>' + obj.kind + '</td><td><strong><a href="javascript:display_boundary(\'' + obj.slug + '\');">' + obj.name + '</a></strong></td></td>';

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
		strokeColor: "#FF7800",
		strokeOpacity: 1,
		strokeWeight: 2,
		fillColor: "#46461F",
		fillOpacity: 0.25
	});

    displayed_slug = slug;
    displayed_polygon.setMap(map);

    if (!no_fit) {
        map.fitBounds(bounds);
    }
}

$(document).ready(function() {
    // Setup handlers
    $('#not-where-i-am').click(function() {
        $(this).hide();
        $('#location-form').fadeIn();
    });
    
    // Clear input box on click, replace value on blur
    defaultval = $('#location-form input[type=text]').val(); 
    $('#location-form input[type=text]').focus(function() {
        if( this.value == defaultval ) {
            $(this).val("");
        }
    });

    // Process address geocoding
    var query = {% if address %}'{{ address }}'{% else %}null{% endif %};

    // Decide what location info to use
    if (query) {
        geocode(query);
    } else if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(geolocation_success, geolocation_error);
    } else {
        // If the browser isn't geo-capable, tell the user.
        $('#georesults').html('<p>Your browser does not support geolocation.</p>');
    }
});

