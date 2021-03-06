Ext.application({
    name : 'portal',

    //Here we build our GUI from existing components - this function should only be assembling the GUI
    //Any processing logic should be managed in dedicated classes - don't let this become a
    //monolithic 'do everything' function
    launch : function() {

        //Send these headers with every AJax request we make...
        Ext.Ajax.defaultHeaders = {
            'Accept-Encoding': 'gzip, deflate' //This ensures we use gzip for most of our requests (where available)
        };

        var urlParams = Ext.Object.fromQueryString(window.location.search.substring(1));
        var isDebugMode = urlParams.debug;


        //Create our store for holding the set of
        //layers that have been added to the map
        var layerStore = Ext.create('portal.layer.LayerStore', {});

        //We need something to handle the clicks on the map
        var queryTargetHandler = Ext.create('portal.layer.querier.QueryTargetHandler', {});

        //Create our map implementations
        var mapCfg = {
            container : null,   //We will be performing a delayed render of this map
            layerStore : layerStore,
            allowDataSelection : true,
            portalIsHandlingLayerSwitcher : true,
            listeners : {
                query : function(mapWrapper, queryTargets) {
                    queryTargetHandler.handleQueryTargets(mapWrapper, queryTargets);
                }
            }
        };
        var urlParams = Ext.Object.fromQueryString(window.location.search.substring(1));
        var map = null;
        if (urlParams && urlParams.map && urlParams.map === 'googleMap') {
            map = Ext.create('portal.map.gmap.GoogleMap', mapCfg);
        } else {
            map = Ext.create('portal.map.openlayers.OpenLayersMap', mapCfg);
        }

        var layerFactory = Ext.create('portal.layer.LayerFactory', {
            map : map,
            formFactory : Ext.create('vegl.layer.filterer.VeglFormFactory', {map : map}),
            downloaderFactory : Ext.create('vegl.layer.VeglDownloaderFactory', {map: map}),
            querierFactory : Ext.create('vegl.layer.VeglQuerierFactory', {map: map}),
            rendererFactory : Ext.create('vegl.layer.VeglRendererFactory', {map: map})
        });

        //Utility function for adding a new layer to the map
        //record must be a CSWRecord or KnownLayer
        var handleAddRecordToMap = function(sourceGrid, record) {
            if (!(record instanceof Array)) {
                record = [record];
            }

            for( var z = 0; z < record.length; z++) {
                var newLayer = null;

                //Ensure the layer DNE first
                var existingRecord = layerStore.getById(record[z].get('id'));
                if (existingRecord) {
                    layersPanel.getSelectionModel().select([existingRecord], false);
                    return;
                 }

                //Turn our KnownLayer/CSWRecord into an actual Layer
                if (record[z] instanceof portal.csw.CSWRecord) {
                    newLayer = record[z].get('layer');
                } else {
                    newLayer = record[z].get('layer');
                }

                //if newLayer is undefined, it must have come from some other source like mastercatalogue
                if (!newLayer){
                    newLayer = layerFactory.generateLayerFromCSWRecord(record[z])
                    //we want it to display immediately.
                    newLayer.set('displayed',true);
                }

                //We may need to show a popup window with copyright info
                var cswRecords = newLayer.get('cswRecords');
                for (var i = 0; i < cswRecords.length; i++) {
                    if (cswRecords[i].hasConstraints()) {
                        var popup = Ext.create('portal.widgets.window.CSWRecordConstraintsWindow', {
                            width : 625,
                            cswRecords : cswRecords
                        });

                        popup.show();

                        //HTML images may take a moment to load which stuffs up our layout
                        //This is a horrible, horrible workaround.
                        var task = new Ext.util.DelayedTask(function(){
                            popup.doLayout();
                        });
                        task.delay(1000);

                        break;
                    }
                }

                layerStore.insert(0,newLayer); //this adds the layer to our store
                layersPanel.getSelectionModel().select([newLayer], false); //this ensures it gets selected
            }
        };

        /**
         * Used as a placeholder for the tree and details panel on the left of screen
         */
        var westPanel = {
            layout: 'border',//VT: vbox doesn't support splitbar unless we custom it.
            region:'west',
            border: false,
            split:true,
            margin:'60 0 0 3',
            width: 370,
            items:[{
                xtype: 'facetedsearchpanel',
                id: 'vlsearchpanel',
                region: 'center',
                map: map,
                layerFactory: layerFactory
            },{
                items : [{xtype: 'ANVGLFooter'}],
                layout : 'fit',
                region :'south'
            }]
        };

        /**
         * This center panel will hold the google maps instance
         */
        var centerPanel = Ext.create('Ext.panel.Panel', {
            region: 'center',
            id: 'center_region',
            margin: '60 0 0 0',
            border: false,
            html : "<div style='width:100%; height:100%' id='center_region-map'></div>",
            listeners: {
                afterrender: function () {
                    map.renderToContainer(centerPanel,'center_region-map');   //After our centerPanel is displayed, render our map into it
                }
            }
        });



        /**
         * Add all the panels to the viewport
         */
        var viewport = Ext.create('Ext.container.Viewport', {
            layout:'border',
            items:[westPanel, centerPanel]
        });

        var activeLayersPanel = Ext.create('Ext.panel.Panel', {
            id : 'activeLayersPanel',
            title : 'Active Layers',
             layout: {
                 type: 'vbox',         // Arrange child items vertically
                 align: 'stretch',     // Each takes up full width
                 padding: 1
             },
             renderTo: Ext.getBody(),
             items : [{
                      xtype: 'activelayerpanel',
                      store : layerStore,
                      //onlineResourcePanelType : 'gaonlineresourcespanel',
                      serviceInformationIcon: 'img/information.png',
                      //mapExtentIcon: 'img/extent3.png',
                      map : map,
                      layerFactory : layerFactory,
                      tooltip : {
                          anchor : 'top',
                          title : 'Featured Layers',
                          text : '<p>This is where the portal groups data services with a common theme under a layer. This allows you to interact with multiple data providers using a common interface.</p><br><p>The underlying data services are discovered from a remote registry. If no services can be found for a layer, it will be disabled.</p>',
                          showDelay : 100,
                          icon : 'img/information.png',
                          dismissDelay : 30000
                      }
                  },{
                     xtype : 'label',
                     id : 'baseMap',
                     html : '<div id="layerSwitcher"></div>',
                     listeners: {
                         afterrender: function (view) {
                             map._drawOpenLayerSwitcher('layerSwitcher');
                         }
                     }
                  }
             ],
             minHeight: 170,
             width: 500,
             collapsible: true,
             collapsed: true,
             animCollapse : true,
             collapseDirection : 'top'
        });
        layerStore.on('add', function() {
            var alp = Ext.getCmp('activeLayersPanel');

            if (alp.getCollapsed()) {
                alp.expand();
                alp.down('activelayerpanel')._updateEmptyText();
            }
        });

        activeLayersPanel.show();
        activeLayersPanel.setZIndex(1000);
        activeLayersPanel.anchorTo(Ext.getBody(), 'tr-tr', [0, 100], true);


        // The subset button needs a handler for when the user draws a subset bbox on the map:
        map.on('dataSelect', function(map, bbox, intersectedRecords) {
          //Show a dialog allow users to confirm the selected data sources
          if (intersectedRecords.length > 0) {
              Ext.create('Ext.Window', {
                  width : 710,
                  maxHeight : 400,
                  title : 'Confirm which datasets you wish to select',
                  modal : true,
                  autoScroll : true,
                  items : [{
                      xtype : 'dataselectionpanel',
                      region : bbox,
                      itemId : 'dataselection-panel',
                      cswRecords : intersectedRecords
                  }],
                  buttons : [{
                      text : 'Capture Data',
                      iconCls : 'add',
                      align : 'right',
                      scope : this,
                      handler : function(btn) {
                          var parentWindow = btn.findParentByType('window');
                          var panel = parentWindow.getComponent('dataselection-panel');

                          panel.saveCurrentSelection(function(totalSelected, totalErrors) {
                              if (totalSelected === 0) {
                                  Ext.Msg.alert('No selection', 'You haven\'t selected any data to capture. Please select one or more rows by checking the box alongside each row.');
                              } else if (totalErrors === 0) {
                                  Ext.Msg.alert('Request Saved', 'Your ' + totalSelected + ' dataset(s) have been saved. You can either continue selecting more data or <a href="jobbuilder.html">create a job</a> to process your existing selections.');
                                  parentWindow.close();
                              } else {
                                  Ext.Msg.alert('Error saving data', 'There were one or more errors when saving some of the datasets you selected');
                                  parentWindow.close();
                              }
                          });
                      }
                  }]
              }).show();
          }

        });

        //Create our permalink generation handler
        var permalinkHandler = function() {
            var mss = Ext.create('portal.util.permalink.MapStateSerializer');

            mss.addMapState(map);
            mss.addLayers(layerStore);

            mss.serialize(function(state, version) {
                var popup = Ext.create('portal.widgets.window.PermanentLinkWindow', {
                    state : state,
                    version : version
                });

                popup.show();
            });
        };
        Ext.get('permalink').on('click', permalinkHandler);
        Ext.get('permalinkicon').on('click', permalinkHandler);

        //Handle deserialisation -- ONLY if we have a uri param called "state".
        var deserializationHandler;
        var urlParams = Ext.Object.fromQueryString(window.location.search.substring(1));
        if (urlParams && (urlParams.state || urlParams.s)) {
            var decodedString = urlParams.state ? urlParams.state : urlParams.s;
            var decodedVersion = urlParams.v;

            deserializationHandler = Ext.create('portal.util.permalink.DeserializationHandler', {
                layerFactory : layerFactory,
                layerStore : layerStore,
                map : map,
                stateString : decodedString,
                stateVersion : decodedVersion
            });

        }
    }
});
