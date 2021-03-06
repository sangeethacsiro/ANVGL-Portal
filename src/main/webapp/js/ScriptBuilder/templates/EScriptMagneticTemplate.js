/**
 * A template for generating a eScript magnetic inversion example.
 */
Ext.define('ScriptBuilder.templates.EScriptMagneticTemplate', {
    extend : 'ScriptBuilder.templates.BaseTemplate',

    description : null,
    name : null,

    constructor : function(config) {
        this.callParent(arguments);
    },

    /**
     * See parent description
     */
    requestScript : function(callback) {
        var jobId = this.wizardState.jobId;
        var maxThreads = this.wizardState.ncpus;

        this._getTemplatedScriptGui(callback, 'escript-magnetic.py', {
            xtype : 'form',
            width : 540,
            height : 410,
            items : [{
                xtype : 'combo',
                fieldLabel : 'Dataset',
                name : 'inversion-file',
                allowBlank : false,
                valueField : 'localPath',
                displayField : 'localPath',
                anchor : '-20',
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: 'The path to a NetCDF input file.'
                }],
                store : Ext.create('Ext.data.Store', {
                    model : 'vegl.models.Download',
                    proxy : {
                        type : 'ajax',
                        url : 'secure/getAllJobInputs.do',
                        extraParams : {
                            jobId : jobId
                        },
                        reader : {
                            type : 'json',
                            rootProperty : 'data'
                        }
                    },
                    autoLoad : true
                })
            },{
                xtype : 'numberfield',
                fieldLabel : 'Max Threads',
                anchor : '-20',
                name : 'n-threads',
                value : maxThreads,
                allowBlank : false,
                minValue : 1,
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: Ext.String.format('The maximum number of execution threads to run (this job will have {0} CPUs)', maxThreads)
                }]
            },{
                xtype: 'fieldcontainer',
                fieldLabel: 'Background B',
                msgTarget: 'under',
                anchor: '100%',
                layout: {
                    type: 'hbox',
                    defaultMargins: {top: 0, right: 5, bottom: 0, left: 0}
                },
                defaults: {
                    hideLabel: true,
                    decimalPrecision : 8
                },
                items: [
                    {xtype: 'displayfield', value: '('},
                    {xtype: 'numberfield',  name: 'bb-north', width: 80, value: 29800},
                    {xtype: 'displayfield', value: 'North ) ('},
                    {xtype: 'numberfield',  name: 'bb-east', width: 80, value: 2780},
                    {xtype: 'displayfield', value: 'East ) ('},
                    {xtype: 'numberfield',  name: 'bb-vertical', width: 80, value: -44000},
                    {xtype: 'displayfield', value: 'Vertical )'}
                ],
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: 'The background magnetic flux density in <b>nano Tesla</b>. Values for Australia can be calculated at the <a href="http://www.ga.gov.au/oracle/geomag/agrfform.jsp" target="_blank">Geoscience Australia website</a>'
                }]
            },{
                xtype : 'numberfield',
                fieldLabel : 'Max Depth',
                anchor : '-20',
                name : 'max-depth',
                value : 40000,
                allowBlank : false,
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: 'The maximum depth of the inversion (in meters).'
                }]
            },{
                xtype : 'numberfield',
                fieldLabel : 'Air Buffer',
                anchor : '-20',
                name : 'air-buffer',
                value : 6000,
                allowBlank : false,
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: 'buffer zone above data (in meters; 6-10km recommended)'
                }]
            },{
                xtype : 'numberfield',
                fieldLabel : 'Z Mesh Elements',
                anchor : '-20',
                name : 'vertical-mesh-elements',
                value : 25,
                allowDecimals : false,
                allowBlank : false,
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: 'Number of mesh elements in vertical direction (approx 1 element per 2km recommended)'
                }]
            },{
                xtype : 'numberfield',
                fieldLabel : 'X Padding',
                anchor : '-20',
                name : 'x-padding',
                value : 0.2,
                minValue : 0,
                maxValue : 1,
                step : 0.1,
                allowBlank : false,
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: 'The amount of horizontal padding in the X direction. This affects end result, about 20% recommended'
                }]
            },{
                xtype : 'numberfield',
                fieldLabel : 'Y Padding',
                anchor : '-20',
                name : 'y-padding',
                value : 0.2,
                allowBlank : false,
                minValue : 0,
                maxValue : 1,
                step : 0.1,
                plugins: [{
                    ptype: 'fieldhelptext',
                    text: 'The amount of horizontal padding in the Y direction. This affects end result, about 20% recommended'
                }]
            }]
        });
    }

});

