// Geocoder stuff
var geocoder = new google.maps.Geocoder();
var map = null;

var displayed_polygon = null;
var boundaries = new Array();

function handle_geocode(results, status) {
    position = new Object();
    position.coords = new Object();
    
    lat = results[0].geometry.location.lat();
    lng = results[0].geometry.location.lng();
    
    // position object
    position.coords.latitude = lat;
    position.coords.longitude = lng;
    position.coords.accuracy = null;
    position.coords.altitude = null;
    position.coords.altitudeAccuracy = null;
    position.coords.heading = null;
    position.coords.speed = null;
    
    exportPosition(position);
}

function geocode(address) {
    // geocode request
    gr = { 'address': address };
    geocoder.geocode(gr, handle_geocode);
}

// Browser geolocation stuff
function googleMapShow(lat,long) {
    var latlng = new google.maps.LatLng(lat, long);
    var myOptions = {
        zoom: 14,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
    
    var markerOpts = {
        position: latlng, 
        map: map
    };
    var mark = new google.maps.Marker(markerOpts);
}

// Use jQuery to display useful information about our position.
function exportPosition(position) {
    $('#georesults').html(
        '<div id="map_canvas" style="float: right; width: 440px; height: 250px; border: 2px solid #ccc"></div>' +
        '<p>' 
                + 'Latitude: ' + position.coords.latitude + '<br />'
                + 'Longitude: ' + position.coords.longitude + '<br />'
                + 'Accuracy: ' + position.coords.accuracy + '<br />'
                + 'Altitude: ' + position.coords.altitude + '<br />'
                + 'Altitude accuracy: ' + position.coords.altitudeAccuracy + '<br />'
                + 'Heading: ' + position.coords.heading + '<br />'
                + 'Speed: ' + position.coords.speed + '<br />'
        + '</p>'
    );
    googleMapShow(position.coords.latitude, position.coords.longitude,{ maximumAge:600000 });
    get_boundaries(position.coords.latitude, position.coords.longitude);
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

// Other stuff
$(function(){
    // Show search form
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
    
});

// And so it begins...
var query = {% if address %}'{{ address }}'{% else %}null{% endif %};

// Decide what location info to use
if ( query ) {
    geocode(query);
} else if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(exportPosition, errorPosition);
} else {
    // If the browser isn't geo-capable, tell the user.
    $('#georesults').html('<p>Your browser does not support geolocation.</p>');
}

