/**
 * A Ext.grid.Panel specialisation for rendering the logs (if any)
 * for a particular job.
 *
 */
Ext.define('vegl.widgets.JobLogsPanel', {
    extend : 'portal.widgets.tab.ActivePreRenderTabPanel',
    alias : 'widget.joblogspanel',

    currentJob : null,

    constructor : function(config) {

        Ext.apply(config, {
            autoScroll : true,
            items : [],
            dockedItems: [{
                xtype: 'toolbar',
                dock: 'bottom',
                items: [{
                    xtype: 'tbfill'
                },{
                    xtype: 'button',
                    text: 'Refresh',
                    iconCls: 'refresh-icon',
                    scope: this,
                    handler: function() {
                        if (this.currentJob) {
                            this.listLogsForJob(this.currentJob);
                        }
                    }
                }]
            }]
        });

        this.callParent(arguments);

        this.clearLogs(true);
    },

    /**
     * Reloads this store with all the jobs for the specified series
     */
    listLogsForJob : function(job) {
        if (job.get('status') === vegl.models.Job.STATUS_UNSUBMITTED) {
            this.clearLogs(true, 'This job hasn\'t been submitted yet.');
            this.currentJob = job;
            return;
        }

        var loadMaskElement = null;
        if (this.rendered) {
            loadMaskElement = this.getEl();
            loadMaskElement.mask('Loading logs...');
        }

        this.clearLogs();
        this.currentJob = job;

        Ext.Ajax.request({
            url : 'secure/getSectionedLogs.do',
            params : {
                jobId : job.get('id')
            },
            scope : this,
            callback : function(options, success, response) {
                if (loadMaskElement) {
                    loadMaskElement.unmask();
                }

                if (!success) {
                    this.clearLogs(true, 'Error communicating with the server.');
                    return;
                }

                var responseObj = Ext.JSON.decode(response.responseText);
                if (!responseObj || !responseObj.success) {
                    this.addEmptyTab('Couldn\'t find any logs for the selected job: ' + responseObj.msg);
                    return;
                }

                var sections = responseObj.data[0];
                var components = [];

                for (var sectionName in sections) {
                    components.push({
                        title : sectionName,
                        itemId : sectionName,
                        autoDestroy : true,
                        layout : 'fit',
                        items: [{
                            xtype: 'panel',
                            border: false,
                            padding: 5,
                            scrollable: true,
                            html: '<iframe sectionName="' + sectionName + '" style="width:100%;height:100%;border:0px;"></iframe>',
                            bodyStyle: {
                                padding: '0px',
                                border: '0px'
                            },
                            listeners: {
                                afterrender: function(panel) {
                                    var iframe = panel.getEl().down('iframe');
                                    var doc = iframe.dom.contentWindow.document;
                                    doc.open();
                                    doc.write(sections[iframe.getAttribute('sectionName')]);
                                    doc.close();
                                    doc.body.setAttribute('style', 'white-space:pre;font-family:monospace;');
                                }
                            }
                        }]
                    });
                }

                //Add our components and select the python tab (if it exists, otherwise use the 'Full' tab)
                if (components.length > 0) {
                    this.add(components);
                    if (!this.setActiveTab('Python')) {
                        this.setActiveTab('Full');
                    }
                } else {
                    this.clearLogs();
                    this.addEmptyTab('The selected job hasn\'t recorded any logs yet.');
                }
            }
        });
    },

    /**
     * Removes logs from this panel. Optionally adds a replacement tab indicating this panel is empty
     */
    clearLogs : function(addEmptyTab, emptyTabMsg) {
        this.currentJob = null;
        this.removeAll(true);
        if (addEmptyTab) {
            this.addEmptyTab(emptyTabMsg ? emptyTabMsg : 'No job selected.');
        }
        this.doLayout();
    },

    /**
     * Adds an empty tab with the specified text to this panel
     */
    addEmptyTab : function(text) {
        this.add({
            autoDestroy : true,
            html : Ext.util.Format.format('<p class="centeredlabel">{0}</p>', text)
        });
    }
});