import simplejson as json
import datetime
import math

class tzwhere(object):
    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    
    
    def __init__(self, file='tz_world.json'):
        featureCollection = json.load(open(file, 'r'))
        self.timezoneNamesToPolygons = {}
        for feature in featureCollection['features']:
            
            tzname = feature['properties']['TZID']
            region = tzname.split('/')[0]
            if feature['geometry']['type'] == 'Polygon':
                polys = feature['geometry']['coordinates']
                if polys and not (tzname in self.timezoneNamesToPolygons):
                    self.timezoneNamesToPolygons[tzname] = []
                  
                for raw_poly in polys:
                    #WPS84 coordinates are [long, lat], while many conventions are [lat, long]
                    #Our data is in WPS84.  Convert to an explicit format which geolib likes.
                    poly = [{'lat': lat, 'lng': lng} for lng, lat in raw_poly];
                    self.timezoneNamesToPolygons[tzname].append(poly)
        self.timezoneLongitudeShortcuts = {};
        self.timezoneLatitudeShortcuts = {};
        for tzname in self.timezoneNamesToPolygons:
            for polyIndex, poly in enumerate(self.timezoneNamesToPolygons[tzname]):
                lats = [x['lat'] for x in poly]
                lngs = [x['lng'] for x in poly]
                minLng = math.floor(min(lngs) / self.SHORTCUT_DEGREES_LONGITUDE) * self.SHORTCUT_DEGREES_LONGITUDE;
                maxLng = math.floor(max(lngs) / self.SHORTCUT_DEGREES_LONGITUDE) * self.SHORTCUT_DEGREES_LONGITUDE;
                minLat = math.floor(min(lats) / self.SHORTCUT_DEGREES_LATITUDE) * self.SHORTCUT_DEGREES_LATITUDE;
                maxLat = math.floor(max(lats) / self.SHORTCUT_DEGREES_LATITUDE) * self.SHORTCUT_DEGREES_LATITUDE;
                degree = minLng
                while degree <= maxLng:
                    if degree not in self.timezoneLongitudeShortcuts:
                        self.timezoneLongitudeShortcuts[degree] = {}
                      
                    if tzname not in self.timezoneLongitudeShortcuts[degree]:
                        self.timezoneLongitudeShortcuts[degree][tzname] = []
                      
                    self.timezoneLongitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + self.SHORTCUT_DEGREES_LONGITUDE
                  
                degree = minLat
                while degree <= maxLat:
                    if degree not in self.timezoneLatitudeShortcuts:
                        self.timezoneLatitudeShortcuts[degree] = {}
                      
                    if tzname not in self.timezoneLatitudeShortcuts[degree]:
                        self.timezoneLatitudeShortcuts[degree][tzname] = []
                      
                    self.timezoneLatitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + self.SHORTCUT_DEGREES_LATITUDE
                    
    def _point_inside_polygon(self, x, y, poly):
        n = len(poly)
        inside =False
    
        p1x, p1y = poly[0]['lng'], poly[0]['lat']
        for i in range(n+1):
            p2x,p2y = poly[i % n]['lng'], poly[i % n]['lat']
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x,p1y = p2x,p2y
    
        return inside
                
    def tzNameAt(self, latitude, longitude):
        latTzOptions = self.timezoneLatitudeShortcuts[math.floor(latitude / self.SHORTCUT_DEGREES_LATITUDE) * self.SHORTCUT_DEGREES_LATITUDE]
        latSet = set(latTzOptions.keys());
        lngTzOptions = self.timezoneLongitudeShortcuts[math.floor(longitude / self.SHORTCUT_DEGREES_LONGITUDE) * self.SHORTCUT_DEGREES_LONGITUDE]
        lngSet = set(lngTzOptions.keys())
        possibleTimezones = lngSet.intersection(latSet);
        if possibleTimezones:
            if False and len(possibleTimezones) == 1:
                return possibleTimezones.pop()
            else:
                for tzname in possibleTimezones:
                    polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]));
                    for polyIndex in polyIndices:
                        poly = self.timezoneNamesToPolygons[tzname][polyIndex];
                        if self._point_inside_polygon(longitude, latitude, poly):
                            return tzname

if __name__ == "__main__":
    w=tzwhere()
    print w.tzNameAt(float(35.295953), float(-89.662186)) #Arlington, TN
    print w.tzNameAt(float(33.58), float(-85.85)) #Memphis, TN
    print w.tzNameAt(float(61.17), float(-150.02)) #Anchorage, AK
    print w.tzNameAt(float(44.12), float(-123.22)) #Eugene, OR
    print w.tzNameAt(float(42.652647), float(-73.756371)) #Albany, NY