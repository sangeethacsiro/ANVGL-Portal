<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "http://www.w3.org/TR/html4/loose.dtd">

<!-- Credits for icons from http://www.fatcow.com/free-icons/ under http://creativecommons.org/licenses/by/3.0/us/-->
<html xmlns:v="urn:schemas-microsoft-com:vml">
   <head>
      <title>VGL Portal</title>

      <meta name="description" content="Access geoscientific information from around Australia, via AuScopes national e-Research infrastructure.">
      <meta name="keywords" content="AuScope, Discovery, Resources, GeoSciML, Mineral Occurrence, Geologic Unit, Australia">
      <meta name="author" content="AuScope">

      <%-- Open Layers Imports --%>
      <link rel="stylesheet" href="portal-core/js/OpenLayers-2.13.1/theme/default/style.css" type="text/css">
      <script src="portal-core/js/OpenLayers-2.13.1/OpenLayers.debug.js" type="text/javascript"></script>

      <script type="text/javascript">
         var VOCAB_SERVICE_URL = "${vocabServiceUrl}";
         var NVCL_WEB_SERVICE_IP = "${nvclWebServiceIP}";
         var WEB_CONTEXT = '<%= request.getContextPath() %>';
         var NEW_SESSION = "${isNewSession}";
      </script>

          
      <%-- JS imports - relative paths back to the webapp directory --%>
      <jsp:include page="../../portal-core/jsimports.jsp"/>
      <jsp:include page="../../portal-core/jsimports-openlayers.jsp"/>
      <jsp:include page="../../jsimports.htm"/>
      
      <%-- CSS imports - relative paths back to the webapp directory--%>
      <jsp:include page="../../portal-core/cssimports.jsp"/>
      <jsp:include page="../../cssimports.htm"/>

      <!-- To enable text selection within a Ext JS GridPanel -->
      <style type="text/css">
        .x-selectable, .x-selectable * {
            -moz-user-select: text!important;
            -khtml-user-select: text!important;
        }
        </style>
        
        <!-- To hide the Overlays in our open layers -->
        <style type="text/css">
        div.dataLayersDiv {
            display: none;
        }
        div.dataLbl {
        	display: none;
        }
        </style>
        
      <link rel="shortcut icon" href="img/favicon.ico" type="image/x-icon" />

      <script src="js/vegl/models/Download.js" type="text/javascript"></script>
   </head>

   <body>
      <!-- Include Navigation Header -->
      <%@ include file="page_header.jsp" %>
      <%@ include file="page_footer.jsp" %>
   </body>

</html>