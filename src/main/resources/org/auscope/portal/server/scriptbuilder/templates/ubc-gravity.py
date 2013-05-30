#!/usr/bin/env python

# VEGL processing script.
# Please load the Job Object before you load other components

import subprocess, csv, math, os, sys, urllib, glob;

# Autogenerated Getter/Setter class
class VEGLBBox:
    _srs = None
    _maxNorthing = None
    _minNorthing = None
    _maxEasting = None
    _minEasting = None

    def __init__(self, srs, maxNorthing, minNorthing, maxEasting, minEasting):
        self._srs = srs
        self._maxNorthing = maxNorthing
        self._minNorthing = minNorthing
        self._maxEasting = maxEasting
        self._minEasting = minEasting

    def getSrs(self):
        return self._srs

    def getMaxNorthing(self):
        return self._maxNorthing

    def getMinNorthing(self):
        return self._minNorthing

    def getMaxEasting(self):
        return self._maxEasting

    def getMinEasting(self):
        return self._minEasting


    # Returns true if the specified northing/easting (assumed to be in the same SRS)
    # lies within the spatial area represented by this bounding box.
    def isPointInsideArea(self, northing, easting):
        return ((easting >= self._minEasting) and (easting <= self._maxEasting) and (northing >= self._minNorthing) and (northing <= self._maxNorthing))

# Autogenerated Getter/Setter class
class VEGLParameters:

    _selectionMinEasting = None
    _selectionMaxEasting = None
    _selectionMinNorthing = None
    _selectionMaxNorthing = None
    _mgaZone = None
    _cellX = None
    _cellY = None
    _cellZ = None
    _inversionDepth = None
    _inputCsvFile = None

    def __init__(self, inputCsvFile, selectionMinEasting, selectionMaxEasting, selectionMinNorthing, selectionMaxNorthing, mgaZone, cellX, cellY, cellZ, inversionDepth):
        self._inputCsvFile = inputCsvFile
        self._selectionMinEasting = selectionMinEasting
        self._selectionMaxEasting = selectionMaxEasting
        self._selectionMinNorthing = selectionMinNorthing
        self._selectionMaxNorthing = selectionMaxNorthing
        self._mgaZone = mgaZone
        self._cellX = cellX
        self._cellY = cellY
        self._cellZ = cellZ
        self._inversionDepth = inversionDepth

    def getInputCsvFile(self):
        return self._inputCsvFile

    def getSelectionMinEasting(self):
        return self._selectionMinEasting

    def getSelectionMaxEasting(self):
        return self._selectionMaxEasting

    def getSelectionMinNorthing(self):
        return self._selectionMinNorthing

    def getSelectionMaxNorthing(self):
        return self._selectionMaxNorthing

    def getMgaZone(self):
        return self._mgaZone

    def getCellX(self):
        return self._cellX

    def getCellY(self):
        return self._cellY

    def getCellZ(self):
        return self._cellZ

    def getInversionDepth(self):
        return self._inversionDepth

    # Gets an instance of VEGLBBox representing the padded bounds
    def getSelectedBounds(self):
        return VEGLBBox(srs=self._mgaZone, maxNorthing=self._selectionMaxNorthing, maxEasting=self._selectionMaxEasting, minNorthing=self._selectionMinNorthing, minEasting=self._selectionMinEasting)

# Global parameter instance for reference
VEGLParams = VEGLParameters(inputCsvFile='${job-input-file}', selectionMinEasting=${job-selection-mineast}, selectionMaxEasting=${job-selection-maxeast}, selectionMinNorthing=${job-selection-minnorth}, selectionMaxNorthing=${job-selection-maxnorth}, mgaZone='${job-mgazone}', cellX=${job-cellx}, cellY=${job-celly}, cellZ=${job-cellz}, inversionDepth=${job-inversiondepth})

# ----- Autogenerated AWS Utility Functions -----
# Uploads inFilePath to the specified bucket with the specified key
def cloudUpload(inFilePath, cloudKey):
    cloudBucket = os.environ["STORAGE_BUCKET"]
    cloudDir = os.environ["STORAGE_BASE_KEY_PATH"]
    queryPath = (cloudBucket + "/" + cloudDir + "/" + cloudKey).replace("//", "/")
    retcode = subprocess.call(["cloud", "upload", cloudKey, inFilePath, "--set-acl=public-read"])
    print ("cloudUpload: " + inFilePath + " to " + queryPath + " returned " + str(retcode))

# downloads the specified key from bucket and writes it to outfile
def cloudDownload(cloudKey, outFilePath):
    cloudBucket = os.environ["STORAGE_BUCKET"]
    cloudDir = os.environ["STORAGE_BASE_KEY_PATH"]
    queryPath = (cloudBucket + "/" + cloudDir + "/" + cloudKey).replace("//", "/")
    retcode = subprocess.call(["cloud", "download",cloudBucket,cloudDir,cloudKey, outFilePath])
    print "cloudDownload: " + queryPath + " to " + outFilePath + " returned " + str(retcode)
# -----------------------------------------------

#------------------------------------------------------------------------------
# supporting methods (and dragons, too) go here
#------------------------------------------------------------------------------
# GLOBAL VARIABLES, USED FOR PROJECTION STUFF
east = 0.0
north = 0.0
#too lazy to properly refactor code used for UTM stuff
pi = math.pi
#these are based on WGS84
#TODO modify for GDA94's spheroid (GRS80)
sm_a = 6378137.0
#sm_b different for GDA94 - 6356752.314140
sm_b = 6356752.314
#first eccentric squared different for GDA94
#calculate as sm_EccSquared = 1 - (sm_b^2 / sm_a^2)
sm_EccSquared = 6.69437999013e-03
#Scale factor for UTM coordinates
UTMScaleFactor = 0.9996

# PROJECT
# This method does a nice projection from a latitude and longitude
# to an easting and northing wtihin a specified MGA zone.
# Based on http://home.hiwaay.net/~taylorc/toolbox/geography/geoutm.html
#
# Could be replaced with the Python hook to the Proj/4 stuff:
# http://code.google.com/p/pyproj/
# or Python GDAL bindings
# http://pypi.python.org/pypi/GDAL/
# given I'm not sure what the portal of doom has on it, I might as well
# write some stuff so it Just Works (trademark, Steve Jobs)
# This'll do for now.
def project(lat, lon, zone):
    east = 0.0
    north = 0.0
    east,north = LatLonToUTMXY(lat, lon, int(zone))
    return east,north

# Vestigial stuff from the projection work I borrowed.
# Will remove one day.
#
# DegToRad
def DegToRad(deg):
    return (deg / 180.0 * pi)

# RadToDeg
def RadToDeg(rad):
    return (rad / pi * 180.0)

# ArcLengthOfMeridian
# Computes the ellipsoidal distance from the equator to a point at a
# given latitude.
# Reference: Hoffmann-Wellenhof, B., Lichtenegger, H., and Collins, J.,
# GPS: Theory and Practice, 3rd ed.  New York: Springer-Verlag Wien, 1994.
# Inputs:
#    phi - Latitude of the point, in radians.
# Globals:
#    sm_a - Ellipsoid model major axis.
#    sm_b - Ellipsoid model minor axis.
# Returns:
#    The ellipsoidal distance of the point from the equator, in meters.
def ArcLengthOfMeridian(phi):
    # precalculate n
    n = (sm_a - sm_b) / (sm_a + sm_b)
    # Precalculate alpha
    alpha = ((sm_a + sm_b) / 2.0) * (1.0 + (math.pow (n, 2.0) / 4.0) + (math.pow (n, 4.0) / 64.0))
    # Precalculate beta
    beta = (-3.0 * n / 2.0) + (9.0 * math.pow (n, 3.0) / 16.0) + (-3.0 * math.pow (n, 5.0) / 32.0)
    # Precalculate gamma
    gamma = (15.0 * math.pow (n, 2.0) / 16.0) + (-15.0 * math.pow (n, 4.0) / 32.0)
    # Precalculate delta
    delta = (-35.0 * math.pow (n, 3.0) / 48.0) + (105.0 * math.pow (n, 5.0) / 256.0)
    # Precalculate epsilon
    epsilon = (315.0 * math.pow (n, 4.0) / 512.0)
    # Now calculate the sum of the series and return
    result = alpha * (phi + (beta * math.sin (2.0 * phi)) + (gamma * math.sin (4.0 * phi)) + (delta * math.sin (6.0 * phi)) + (epsilon * math.sin (8.0 * phi)))
    return result

# UTMCentralMeridian
# Determines the central meridian for the given UTM zone.
# Inputs:
#    zone - An integer value designating the UTM zone, range [1,60].
# Returns:
#   The central meridian for the given UTM zone, in radians, or zero
#   if the UTM zone parameter is outside the range [1,60].
#   Range of the central meridian is the radian equivalent of [-177,+177].
def UTMCentralMeridian(zone):
    cmeridian = math.radians(-183.0 + (zone * 6.0))
    return cmeridian

# FootpointLatitude
# Computes the footpoint latitude for use in converting transverse
# Mercator coordinates to ellipsoidal coordinates
# Reference: Hoffmann-Wellenhof, B., Lichtenegger, H., and Collins, J.,
#   GPS: Theory and Practice, 3rd ed.  New York: Springer-Verlag Wien, 1994.
# Inputs:
#   y - The UTM northing coordinate, in meters.
# Returns:
#   The footpoint latitude, in radians.
def FootpointLatitude(y):
    # Precalculate n (Eq. 10.18)
    n = (sm_a - sm_b) / (sm_a + sm_b)
    # Precalculate alpha_ (Eq. 10.22)
    # (Same as alpha in Eq. 10.17)
    alpha_ = ((sm_a + sm_b) / 2.0) * (1 + (math.pow (n, 2.0) / 4) + (math.pow (n, 4.0) / 64))
    # Precalculate y_ (Eq. 10.23)
    y_ = y / alpha_
    # Precalculate beta_ (Eq. 10.22)
    beta_ = (3.0 * n / 2.0) + (-27.0 * math.pow (n, 3.0) / 32.0) + (269.0 * math.pow (n, 5.0) / 512.0)
    # Precalculate gamma_ (Eq. 10.22)
    gamma_ = (21.0 * math.pow (n, 2.0) / 16.0) + (-55.0 * math.pow (n, 4.0) / 32.0)
    # Precalculate delta_ (Eq. 10.22)
    delta_ = (151.0 * math.pow (n, 3.0) / 96.0) + (-417.0 * math.pow (n, 5.0) / 128.0)
    # Precalculate epsilon_ (Eq. 10.22)
    epsilon_ = (1097.0 * math.pow (n, 4.0) / 512.0)
    # Now calculate the sum of the series (Eq. 10.21)
    result = y_ + (beta_ * math.sin (2.0 * y_)) + (gamma_ * math.sin (4.0 * y_)) + (delta_ * math.sin (6.0 * y_)) + (epsilon_ * math.sin (8.0 * y_))
    return result

# MapLatLonToXY
# Converts a latitude/longitude pair to x and y coordinates in the
# Transverse Mercator projection.  Note that Transverse Mercator is not
# the same as UTM; a scale factor is required to convert between them.
# Reference: Hoffmann-Wellenhof, B., Lichtenegger, H., and Collins, J.,
# GPS: Theory and Practice, 3rd ed.  New York: Springer-Verlag Wien, 1994.
# Inputs:
#    phi - Latitude of the point, in radians.
#    lambda - Longitude of the point, in radians.
#    lambda0 - Longitude of the central meridian to be used, in radians.
# Returns:
#    Two values, x and y: x and y coordinates of computed point, not scaled.
def MapLatLonToXY(phi, lambda1, lambda0):
    x = 0.0
    y = 0.0
    # Precalculate ep2
    ep2 = (math.pow(sm_a, 2.0) - math.pow(sm_b, 2.0)) / math.pow(sm_b, 2.0)
    # Precalculate nu2
    nu2 = ep2 * math.pow(math.cos(phi), 2.0)
    # Precalculate N
    N = math.pow(sm_a, 2.0) / (sm_b * math.sqrt(1 + nu2))
    # Precalculate t
    t = math.tan(phi)
    t2 = t * t
    tmp = (t2 * t2 * t2) - math.pow(t, 6.0)
    # Precalculate l
    l = lambda1 - lambda0
    # Precalculate coefficients for l**n in the equations below
    # so a normal human being can read the expressions for easting
    # and northing
    #  -- l**1 and l**2 have coefficients of 1.0
    l3coef = 1.0 - t2 + nu2
    l4coef = 5.0 - t2 + 9 * nu2 + 4.0 * (nu2 * nu2)
    l5coef = 5.0 - 18.0 * t2 + (t2 * t2) + 14.0 * nu2 - 58.0 * t2 * nu2
    l6coef = 61.0 - 58.0 * t2 + (t2 * t2) + 270.0 * nu2 - 330.0 * t2 * nu2
    l7coef = 61.0 - 479.0 * t2 + 179.0 * (t2 * t2) - (t2 * t2 * t2)
    l8coef = 1385.0 - 3111.0 * t2 + 543.0 * (t2 * t2) - (t2 * t2 * t2)
    # Calculate easting (x)
    x = N * math.cos (phi) * l + (N / 6.0 * math.pow (math.cos (phi), 3.0) * l3coef * math.pow (l, 3.0)) + (N / 120.0 * math.pow (math.cos (phi), 5.0) * l5coef * math.pow (l, 5.0)) + (N / 5040.0 * math.pow (math.cos (phi), 7.0) * l7coef * math.pow (l, 7.0))
    # Calculate northing (y)
    y = ArcLengthOfMeridian (phi) + (t / 2.0 * N * math.pow (math.cos (phi), 2.0) * math.pow (l, 2.0)) + (t / 24.0 * N * math.pow (math.cos (phi), 4.0) * l4coef * math.pow (l, 4.0)) + (t / 720.0 * N * math.pow (math.cos (phi), 6.0) * l6coef * math.pow (l, 6.0)) + (t / 40320.0 * N * math.pow (math.cos (phi), 8.0) * l8coef * math.pow (l, 8.0))
    return x,y

# MapXYToLatLon
# TODO: Function not fixed for Python-ness 28/06/2011
# Converts x and y coordinates in the Transverse Mercator projection to
# a latitude/longitude pair.  Note that Transverse Mercator is not
# the same as UTM; a scale factor is required to convert between them.
# Reference: Hoffmann-Wellenhof, B., Lichtenegger, H., and Collins, J.,
#   GPS: Theory and Practice, 3rd ed.  New York: Springer-Verlag Wien, 1994.
# Inputs:
#   x - The easting of the point, in meters.
#   y - The northing of the point, in meters.
#   lambda0 - Longitude of the central meridian to be used, in radians.
# Outputs:
#   philambda - A 2-element containing the latitude and longitude
#                in radians.
# Returns:
#   The function does not return a value.
# Remarks:
#   The local variables Nf, nuf2, tf, and tf2 serve the same purpose as
#   N, nu2, t, and t2 in MapLatLonToXY, but they are computed with respect
#   to the footpoint latitude phif.
#
#   x1frac, x2frac, x2poly, x3poly, etc. are to enhance readability and
#   to optimize computations.
def MapXYToLatLon(x, y, lambda0, philambda):
    # Get the value of phif, the footpoint latitude.
    phif = FootpointLatitude (y)
    # Precalculate ep2
    ep2 = (math.pow (sm_a, 2.0) - math.pow (sm_b, 2.0)) / math.pow (sm_b, 2.0)
    # Precalculate cos (phif)
    cf = math.cos (phif)
    # Precalculate nuf2
    nuf2 = ep2 * math.pow (cf, 2.0)
    # Precalculate Nf and initialize Nfpow
    Nf = math.pow (sm_a, 2.0) / (sm_b * math.sqrt (1 + nuf2))
    Nfpow = Nf
    # Precalculate tf
    tf = math.tan (phif)
    tf2 = tf * tf
    tf4 = tf2 * tf2
    # Precalculate fractional coefficients for x**n in the equations
    # below to simplify the expressions for latitude and longitude.
    x1frac = 1.0 / (Nfpow * cf)
    Nfpow *= Nf            # now equals Nf**2
    x2frac = tf / (2.0 * Nfpow)
    Nfpow *= Nf            # now equals Nf**3
    x3frac = 1.0 / (6.0 * Nfpow * cf)
    Nfpow *= Nf        # now equals Nf**4
    x4frac = tf / (24.0 * Nfpow)
    Nfpow *= Nf        # now equals Nf**5
    x5frac = 1.0 / (120.0 * Nfpow * cf)
    Nfpow *= Nf        # now equals Nf**6
    x6frac = tf / (720.0 * Nfpow)
    Nfpow *= Nf        # now equals Nf**7
    x7frac = 1.0 / (5040.0 * Nfpow * cf)
    Nfpow *= Nf        # now equals Nf**8
    x8frac = tf / (40320.0 * Nfpow)
    # Precalculate polynomial coefficients for x**n.
    #    -- x**1 does not have a polynomial coefficient.
    x2poly = -1.0 - nuf2
    x3poly = -1.0 - 2 * tf2 - nuf2
    x4poly = 5.0 + 3.0 * tf2 + 6.0 * nuf2 - 6.0 * tf2 * nuf2 - 3.0 * (nuf2 *nuf2) - 9.0 * tf2 * (nuf2 * nuf2)
    x5poly = 5.0 + 28.0 * tf2 + 24.0 * tf4 + 6.0 * nuf2 + 8.0 * tf2 * nuf2
    x6poly = -61.0 - 90.0 * tf2 - 45.0 * tf4 - 107.0 * nuf2     + 162.0 * tf2 * nuf2
    x7poly = -61.0 - 662.0 * tf2 - 1320.0 * tf4 - 720.0 * (tf4 * tf2)
    x8poly = 1385.0 + 3633.0 * tf2 + 4095.0 * tf4 + 1575 * (tf4 * tf2)
    # Calculate latitude
    philambda[0] = phif + x2frac * x2poly * (x * x)    + x4frac * x4poly * math.pow (x, 4.0) + x6frac * x6poly * math.pow (x, 6.0) + x8frac * x8poly * math.pow (x, 8.0)
    # Calculate longitude
    philambda[1] = lambda0 + x1frac * x    + x3frac * x3poly * math.pow (x, 3.0) + x5frac * x5poly * math.pow (x, 5.0)    + x7frac * x7poly * math.pow (x, 7.0)
    return

# LatLonToUTMXY
# Converts a latitude/longitude pair to x and y coordinates in the
# Universal Transverse Mercator projection.
# Inputs:
#   lat - Latitude of the point, in degrees.
#   lon - Longitude of the point, in degrees.
#   zone - UTM zone to be used for calculating values for x and y.
#          If zone is less than 1 or greater than 60, the routine
#          will determine the appropriate zone from the value of lon.
# Outputs:
#   xy - A 2-element array where the UTM x and y values will be stored.
# Returns:
#   The UTM zone used for calculating the values of x and y.
def LatLonToUTMXY(lat, lon, zone):
    east,north = MapLatLonToXY(math.radians(lat), math.radians(lon), UTMCentralMeridian (zone))
    # Adjust easting and northing for UTM system.
    # magic number on the easting (500000) is the false easting
    east = east * UTMScaleFactor + 500000.0
    north = north * UTMScaleFactor
    # this is used to add the false northing for southern hemisphere values
    if (north < 0.0):
        north = north + 10000000.0
    return east,north

# UTMXYToLatLon
# Converts x and y coordinates in the Universal Transverse Mercator
# projection to a latitude/longitude pair.
# Inputs:
#    x - The easting of the point, in meters.
#    y - The northing of the point, in meters.
#    zone - The UTM zone in which the point lies.
#    southhemi - True if the point is in the southern hemisphere;
#                false otherwise.
# Outputs:
#    latlon - A 2-element array containing the latitude and
#             longitude of the point, in radians.
# Returns:
#    The function does not return a value.
def UTMXYToLatLon(x, y, zone, southhemi, latlon):
    x -= 500000.0
    x /= UTMScaleFactor
    # If in southern hemisphere, adjust y accordingly.
    if (southhemi):
        y -= 10000000.0
    y /= UTMScaleFactor
    cmeridian = UTMCentralMeridian (zone)
    MapXYToLatLon (x, y, cmeridian, latlon)
    return

#------------------------------------------------------------------------------
# Methods other than function projection stuff down here
#------------------------------------------------------------------------------
# GET_MAG_FIELD
# This is a method which gets the magnetic field things we need
# Needs a latitude and longitude and an 'epoch' - time we want the mag field for
# A few URLs can be used to get this
# http://www.ngdc.noaa.gov/geomag/magfield.shtml
# http://www.ga.gov.au/oracle/geomag/agrfform.jsp
# example of the GA one, using AGRF
# http://www.ga.gov.au/bin/geoAGRF?latd=-24&latm=00&lats=00&lond=135&lonm=00&lons=00&elev=0&year=2010&month=01&day=1&Ein=D
#
#TODO: Make it a bit more awesome
def get_mag_field(lat, lon, year, month, day):
    #some defaults so it doesn't fall over
    declination = 0.0
    inclination = 0.0
    intensity = 50000.0
    #for AGRF call we need decimal degrees turned into lats and lons
    latd,latm,lats = decdeg2dms(lat)
    lond,lonm,lons = decdeg2dms(lon)
    #assume zero elevation
    elev = 0
    #successive formatting of URL to make it a bit easier to read
    #urlencode doesn't work very well for some reason, but this handcoded way does
    #base URL for AGRF online calculation as of 1 July 2011
    base_url = 'http://www.ga.gov.au/bin/geoAGRF?'
    #latitude stuff
    full_url = base_url + 'latd=' + str(latd) + '&latm=' + str(latm) + '&lats=' + str(lats)
    #longitude stuff
    full_url = full_url + '&lond=' + str(lond) + '&lonm=' + str(lonm) + '&lons=' + str(lons)
    #elevation stuff
    full_url = full_url + '&elev=' + str(elev)
    #epoch stuff
    full_url = full_url + '&year=' + str(year) + '&month=' + str(month) + '&day=' + str(day)
    #We want three components - D is declination, I is inclination, F is total field strength
    full_url = full_url + '&Ein=D&Ein=I&Ein=F'

    #debugging: what URL are we retrieving?
    print 'Retrieving the following URL: ' + full_url
    #open the URL, read its full contents into a variable
    f = urllib.urlopen(full_url)
    agrf_page_contents = f.read()

    #now we need to extract the small section of the page we're looking for
    #As of 1 July 2011, it is bounced by <br><b>Magnetic Field Components<br> and a newline</b><br>
    #Find the start string, and 41 characters to this position index to strip out
    #the Magnetic Field Components sentence & formatting characteristics
    start_index = agrf_page_contents.find('<br><b>Magnetic Field Components<br>') + 41
    #End index is easier to define
    end_index = agrf_page_contents.find('\n</b><br>')
    #Extract the text between the two indices we defined above
    components_contents = agrf_page_contents[start_index:end_index]
    #Now we can split them with a newline and <br> delimiter
    #Will provide 3 'component' strings
    for component in components_contents.split('\n<br>'):
        #Check the first character and remove the leading characters
        #and convert the extracted text to a float
        #D means declination...
        if component[0:1] == 'D':
            declination = float(component[4:-3])
        #I means inclination...
        if component[0:1] == 'I':
            inclination = float(component[4:-3])
        #and F means total field intensity
        if component[0:1] == 'F':
            intensity = float(component[4:-3])
    return declination,inclination,intensity

# DECDEG2DMS
# Converts a decimal degree number into degrees, minutes and seconds.
def decdeg2dms(dd):
    mnt,sec = divmod(dd*3600,60)
    deg,mnt = divmod(mnt,60)
    return deg,mnt,sec

#------------------------------------------------------------------------------
# Methods other than function projection stuff down here
#------------------------------------------------------------------------------
# GET_MAG_FIELD_DATA
# This is a method which gets the magnetic field things we need
# Needs a latitude and longitude and an 'epoch' - time we want the mag field for
# A few URLs can be used to get this
# http://www.ngdc.noaa.gov/geomag/magfield.shtml
# http://www.ga.gov.au/oracle/geomag/agrfform.jsp
# example of the GA one, using AGRF
# http://www.ga.gov.au/bin/geoAGRF?latd=-24&latm=00&lats=00&lond=135&lonm=00&lons=00&elev=0&year=2010&month=01&day=1&Ein=D
#
#TODO: Make it a bit more awesome
def get_mag_field_data(lat, lon, year, month, day):
    #some defaults so it doesn't fall over
    declination = 0.0
    inclination = 0.0
    intensity = 50000.0
    #for AGRF call we need decimal degrees turned into lats and lons
    latd,latm,lats = decdeg2dms(lat)
    lond,lonm,lons = decdeg2dms(lon)
    #assume zero elevation
    elev = 0
    #successive formatting of URL to make it a bit easier to read
    #urlencode doesn't work very well for some reason, but this handcoded way does
    #base URL for AGRF online calculation as of 1 July 2011
    base_url = 'http://www.ga.gov.au/bin/geoAGRF?'
    #latitude stuff
    full_url = base_url + 'latd=' + str(latd) + '&latm=' + str(latm) + '&lats=' + str(lats)
    #longitude stuff
    full_url = full_url + '&lond=' + str(lond) + '&lonm=' + str(lonm) + '&lons=' + str(lons)
    #elevation stuff
    full_url = full_url + '&elev=' + str(elev)
    #epoch stuff
    full_url = full_url + '&year=' + str(year) + '&month=' + str(month) + '&day=' + str(day)
    #We want three components - D is declination, I is inclination, F is total field strength
    full_url = full_url + '&Ein=D&Ein=I&Ein=F'

    #debugging: what URL are we retrieving?
    print 'Retrieving the following URL: ' + full_url
    #open the URL, read its full contents into a variable
    f = urllib.urlopen(full_url)
    agrf_page_contents = f.read()

    #now we need to extract the small section of the page we're looking for
    #As of 1 July 2011, it is bounced by <br><b>Magnetic Field Components<br> and a newline</b><br>
    #Find the start string, and 41 characters to this position index to strip out
    #the Magnetic Field Components sentence & formatting characteristics
    start_index = agrf_page_contents.find('<br><b>Magnetic Field Components<br>') + 41
    #End index is easier to define
    end_index = agrf_page_contents.find('\n</b><br>')
    #Extract the text between the two indices we defined above
    components_contents = agrf_page_contents[start_index:end_index]
    #Now we can split them with a newline and <br> delimiter
    #Will provide 3 'component' strings
    for component in components_contents.split('\n<br>'):
        #Check the first character and remove the leading characters
        #and convert the extracted text to a float
        #D means declination...
        if component[0:1] == 'D':
            declination = float(component[4:-3])
        #I means inclination...
        if component[0:1] == 'I':
            inclination = float(component[4:-3])
        #and F means total field intensity
        if component[0:1] == 'F':
            intensity = float(component[4:-3])
    return declination,inclination,intensity
# autogenerated function definition
def main():
    # ------------ VEGL - Step 1 ---------
    f = file(VEGLParams.getInputCsvFile(), "r")
    input_csv = csv.reader(f)
    data = []
    lineCount = 0 # The first 2 lines contain text and must be skipped
    for strX, strY, strZ in input_csv:
        if lineCount > 1:
            x = float(strX)
            y = float(strY)
            z = float(strZ)
            data.append([x,y,z])
        lineCount = lineCount + 1

    # ------------------------------------


    VEGLSelectedBox = VEGLParams.getSelectedBounds()
    zone = int(VEGLSelectedBox.getSrs())
    temp_data = []
    for x, y, z in data:
        newX, newY = project(x, y, zone)
        temp_data.append([newX, newY, z])
    data = temp_data

    temp_data = []
    for x, y, z in data:
        # isPointInsideArea happens to read northings then eastings, and we store
        # northings as y, and eastings as
        if VEGLSelectedBox.isPointInsideArea(y,x):
            temp_data.append([x,y,z])
    data = temp_data

    # If we have a gravity inversion, we need to correct the units of the supplied gravity data.
    # National gravity coverages are in units of micrometres per second squared.
    # UBC-GIF gravity inversion expects milliGals, which means we divide supplied properties by 10.
    #
    i = 0
    for east,north,prop in data:
        data[i] = east,north,prop/10
        i = i + 1

    # UBC-GIF needs a data file in a specific format.
    # We need to define a filename ('obs_filename').
    # This includes writing out expected errors in the data, number of data points etc.
    print 'Time to write out a data file'
    obs_file = 'temp_ubc_obs.asc'
    f = file(obs_file, 'w')
    f.write(str(len(data)) + '\t! Number of points\n')
    # For each data point, write out: Easting, Northing, Elevation, Data, Error
    # In this simple example, we assume elevation is 1 m, and error are 2 mGal / nT
    for east,north,prop in data:
        elevation = 1.0
        error = 2.0
        f.write(str(east) + ' ' + str(north) + ' ' + str(elevation) + ' ' + str(prop) + ' ' + str(error) + '\n')
    f.close()
    # Step 6: calculate some meshy stuff
    # --- Scientific description below ---
    # Defines the mesh parameters and writes out a UBC-GIF mesh file.
    # Mesh is defined by the minimum and maximum eastings and northings, inversion depth, and respective cell sizes.
    # Mesh file name: 'mesh'
    minEasting = VEGLSelectedBox.getMinEasting()
    maxEasting = VEGLSelectedBox.getMaxEasting()
    minNorthing = VEGLSelectedBox.getMinNorthing()
    maxNorthing = VEGLSelectedBox.getMaxNorthing()
    invDepth = VEGLParams.getInversionDepth()
    cell_x = VEGLParams.getCellX()
    cell_y = VEGLParams.getCellY()
    cell_z = VEGLParams.getCellZ()
    num_x_cells = int((maxEasting - minEasting) / cell_x)
    num_y_cells = int((maxNorthing - minNorthing) / cell_y)
    num_z_cells = int(invDepth / cell_z)
    print 'Number of cells in x dimension: ' + str(num_x_cells) + ', number of cells in y dimension: ' + str(num_y_cells) + ' and number of cells in z dimension: ' + str(num_z_cells)
    # Define mesh file name here
    mesh = 'mesh.msh'
    try:
        f = file(mesh, 'w')
        f.write(str(num_x_cells) + ' ' + str(num_y_cells) + ' ' + str(num_z_cells) + '\n')
        f.write(str(minEasting) + ' ' + str(minNorthing) + ' 0\n')
        f.write(str(num_x_cells) + '*' + str(cell_x) + '\n')
        f.write(str(num_y_cells) + '*' + str(cell_y) + '\n')
        f.write(str(num_z_cells) + '*' + str(cell_z))
        f.close()
    except IOError, e:
        print e
        sys.exit(1)

    # Step 7: Write out sensitivity analsysis control file
    # --- Scientific description below ---
    # There are two parts to running a UBC-GIF inversion. The first involves a sensitivity analysis;
    # here we write out the appropriate control files for this analysis.
    # File names for things defined outside this method are defined at the top
    obs_file = 'temp_ubc_obs.asc'
    mesh = 'mesh.msh'
    # Sensitivity analysis (*sen3d_MPI) input file
    sns_inp = 'sens.inp'

    # Write some files
    try:
        f = file(sns_inp, 'w')
        f.write(mesh + ' ! mesh\n')
        f.write(obs_file + ' ! observations file\n')
        f.write('null ! topography\n')
        f.write('2 ! iwt\n')
        f.write('null ! beta, znot\n')
        f.write('daub2 ! wavelet\n')
        f.write('2 1e-4 ! itol eps\n')
        f.close()

    except IOError, e:
        print e
        sys.exit(1)

    # Step 8: Write out inversion control file
    # --- Scientific description below ---
    # In the second part to running a UBC-GIF inversion, we need to write out
    # the control file for the actual inversion.
    # File names for things defined outside this method are defined at the top
    obs_file = 'temp_ubc_obs.asc'
    inv_inp = 'inv.inp'
    try:
        f = file(inv_inp, 'w')
        f.write('0 !irest\n')
        f.write('1 !mode\n')
        f.write('1  0.02 !par tolc\n')
        f.write(obs_file + ' ! observations file\n')
        # file name dependant on type set in JS
        f.write('gzinv3d.mtx\n')
        f.write('null !initial model\n')
        f.write('null !reference model\n')
        f.write('null !active cell file\n')
        f.write('null !lower, upper bounds\n')
        f.write('null Le, Ln, Lz\n')
        f.write('SMOOTH_MOD\n')
        f.write('null !weighting file\n')
        f.write('0\n')
        f.close()
    except IOError, e:
        print e
        sys.exit(1)

    # step 9: finalise stuff - I guess this is where we execute two commands
    # At a guess, they are the two commented-out lines below?
    # Control files, defined elsewhere
    sns_inp = 'sens.inp'
    sns_out = 'sens.out'
    inv_inp = 'inv.inp'
    inv_out = 'inv.out'
    sensitivity_command = 'mpirun -np ${n-threads} --mca btl self,sm /opt/ubc/gzsen3d_MPI ' + sns_inp + ' > ' + sns_out
    inversion_command = 'mpirun -np ${n-threads} --mca btl self,sm /opt/ubc/gzinv3d_MPI ' + inv_inp + ' > ' + inv_out
    print 'Sensitivity command: ' + sensitivity_command
    print 'Inversion command: ' + inversion_command
    sys.stdout.flush()
    retcode = subprocess.call(sensitivity_command, shell=True)
    print 'sensitivity returned: ' + str(retcode)
    sys.stdout.flush()
    retcode = subprocess.call(inversion_command, shell=True)
    print 'inversion returned: ' + str(retcode)
    sys.stdout.flush()
    # Upload our logging outs
    cloudUpload(sns_out, sns_out)
    cloudUpload(inv_out, inv_out)
    # Upload the mesh file
    cloudUpload(mesh, mesh)
    # Upload gravity or magnetic data file
    denFiles = glob.glob('*zinv3d*.den')
    preFiles = glob.glob('*zinv3d*.pre')
    # Upload Final Model + Prediction
    print 'Uploading final model and prediction'
    invFilesToUpload = []
    if len(denFiles) > 0:
        denFiles.sort()
        invFilesToUpload.append(denFiles[len(denFiles) - 1])
    if len(preFiles) > 0:
        preFiles.sort()
        invFilesToUpload.append(preFiles[len(preFiles) - 1])
    print 'About to upload the following files:'
    print invFilesToUpload
    for invFile in invFilesToUpload:
        cloudUpload(invFile, invFile)

# autogenerated main definition
if __name__ == "__main__":
    main()

