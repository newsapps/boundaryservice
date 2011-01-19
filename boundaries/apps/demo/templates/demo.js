// Geocoder stuff
var geocoder = new google.maps.Geocoder();
var map = null;

var user_marker = new google.maps.Marker();
var displayed_polygon = null;
var boundaries = new Array();

function init_map(lat, lng) {
    var ll = new google.maps.LatLng(lat, lng);

    var map_options = {
        zoom: 14,
        center: ll,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    map = new google.maps.Map(document.getElementById("map_canvas"), map_options);
}

function show_user_marker(lat, lng) {
    user_marker.setPosition(new google.maps.LatLng(lat, lng));
    user_marker.setMap(map);
}

function geocode(address) {
    // geocode request
    gr = { 'address': address };
    geocoder.geocode(gr, handle_geocode);
}

function handle_geocode(results, status) {
    position = new Object();
    position.coords = new Object();
    
    lat = results[0].geometry.location.lat();
    lng = results[0].geometry.location.lng();
    
    $('#georesults').html(
        '<div id="map_canvas" style="float: right; width: 440px; height: 250px; border: 2px solid #ccc"></div>' +
        '<p>' 
                + 'Latitude: ' + lat + '<br />'
                + 'Longitude: ' + lng + '<br />'
        + '</p>'
    );

    if (map == null) {
        init_map(lat, lng);
    }
    
    show_user_marker(lat, lng);
    get_boundaries(lat, lng);
}

function errorPosition() {
    $('#georesults').html('<p>The page could not get your location.</p>');
}

// User boundary service to lookup what areas the location falls within
function get_boundaries(lat, lng) {
    var table_html = '<h3>Your location falls within:</h3><table id="boundaries" border="0" cellpadding="0" cellspacing="0">';
    var query_url = 'http://{{ domain }}/api/1.0/boundary/?format=jsonp&limit=100&contains='+lat+','+lng+'&callback=?';
    
    $.getJSON(query_url, function(data) {
        $.each(data.objects, function(i, obj) {
            boundaries[obj.slug] = obj;
            table_html += '<tr><td>' + obj.kind + '</td><td><strong><a href="javascript:display_boundary(\'' + obj.slug + '\');">' + obj.name + '</a></strong></td></td>';
        });
        table_html += '</table>';
        $('#area-lookup').html(table_html);
    });
    
}

function display_boundary(slug) {
    // Clear old polygons
    if (displayed_polygon != null) {
        displayed_polygon.setMap(null);
        displayed_polygon = null;
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

    displayed_polygon.setMap(map);
    map.fitBounds(bounds);
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
        navigator.geolocation.getCurrentPosition(exportPosition, errorPosition);
    } else {
        // If the browser isn't geo-capable, tell the user.
        $('#georesults').html('<p>Your browser does not support geolocation.</p>');
    }
});

