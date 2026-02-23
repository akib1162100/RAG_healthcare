odoo.define('easy_dashboard_app.Dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var rpc = require('web.rpc');
var session = require('web.session');
var web_client = require('web.web_client');
var _t = core._t;
var QWeb = core.qweb;

var DynamicDashboard = AbstractAction.extend({
    template: 'dynamic_dashboard',
    events: {
         'click .add_block': '_onClick_add_block',
         'click .view_tile_items': '_onClick_view_tile_items',
         'click .View_graph_items': '_onClick_view_graph_items',
         'click .add_grapgh': '_onClick_add_grapgh',
         'click .block_setting': '_onClick_block_setting',
         'click .tile': '_onClick_tile',
    },

    init: function(parent, context) {
        this.action_id = context['id'];
        this._super(parent, context);
        this.block_ids = []
    },

    start: function() {
        var self = this;
        this.set("title", 'Dashboard');

        return this._super().then(function() {
            self.render_dashboards();
        });
    },

    willStart: function() {
        var self = this;
        return $.when(this._super()).then(function() {
             return self.fetch_data();
        });
    },

     fetch_data: function() {
        var self = this;
        var def1 =  this._rpc({
                model: 'dashboard.block',
                method: 'get_dashboard_vals',
                args: [[],this.action_id]
            }).then(function(result) {
                self.block_ids = result;
        });
        return $.when(def1);
    },

    get_colors : function(x_axis) {
        var color = []
        var borderColors = []
        for (var j = 0; j < x_axis.length; j++) {
            var r = Math.floor(Math.random() * 255);
            var g = Math.floor(Math.random() * 255);
            var b = Math.floor(Math.random() * 255);
            color.push("rgb(" + r + "," + g + "," + b + ",.5)");
            borderColors.push("rgb(" + r + "," + g + "," + b + ",1)");
         }
         return [color,borderColors]
    },
    get_values_bar: function (block) {
      var labels = block['x_axis'] || ["label1","label2","label3"];
      var colors = this.get_colors(block['x_axis']);
      var borderColors = colors[1];
      var backgroundColor = colors[0];
  
      var data = {
          labels: labels,
          datasets: [{
              label: block['name'],
              data: block['y_axis'] || [4,6,9],
              backgroundColor: backgroundColor,
              borderColor: borderColors, // Border color for bars
              borderWidth: 1,
              borderRadius: 5,
          }]
      };
  
      var options = {
        scales: {
            y: {
                beginAtZero: true
            }
        },
        responsive: true,
        plugins: {
            legend: {
                display: false,
               
            },
            title: {
                display: true,
                text: block['name'] || 'Advanced Line Chart',
                font: {
                    size: 20,
                    weight: 'bold'
                }
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'xy',
                },
                zoom: {
                    enabled: true,
                    mode: 'xy',
                }
            }
        },
        
    };
  
      var bar_data = {
          type: 'bar',
          data: data,
          options: options
      };
      console.log(bar_data)
      return bar_data;
  },
  
  get_values_pie: function (block) {
    // Extract data from the block object
    var labels = block['x_axis'];
    var colors = this.get_colors(block['x_axis']);
    var backgroundColors = colors[0];
    var borderColors = colors[1];

    // Prepare the data object for the Pie Chart
    var data = {
        labels: labels,
        datasets: [{
            label: block['name'] || '',
            data: block['y_axis'],
            backgroundColor: backgroundColors, // Single background color or array of colors
            borderColor: "white", // Single border color or array of colors
            borderWidth: 3, // You can adjust the border width
            hoverOffset: block['hover_offset'] || 4
        }]
    };

    // Define options for the Pie Chart
    var options = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                position: block['legend_position'] || 'bottom',
            },
            title: {
                display: true,
                text: block['chart_title'] || 'Pie Chart',
                font: {
                    weight: 'bold',
                    size:  20 // Set the title font size
                }
            }
        }
    };

        // Combine data and options into a configuration object for the Pie Chart
        var pie_data = {
            type: 'pie',
            data: data,
            options: options
        };

        // Return the configuration object for the Pie Chart
        return pie_data;
},


    get_values_line: function (block) {
      var labels = block['x_axis'];
      var colors = this.get_colors(block['x_axis']);
      var bgColors = colors[0];
      var borderColors = colors[1];
      var data = {
          labels: labels,
          datasets: [{
              label: block['name'],
              data: block['y_axis'],
              fill: true,
              borderColor: 'rgb(201, 201, 201)', // Line color
              borderWidth: 1,
              pointBackgroundColor:  borderColors, // Data point color
              pointBorderColor: bgColors,
              pointBorderWidth: 2,
              tension: .2
          }]
      };
  
      var options = {
        responsive: true,
        plugins: {
            legend: {
                display: false,
               
            },
            title: {
                display: true,
                text: block['name'] || 'Advanced Line Chart',
                font: {
                    size: 20,
                    weight: 'bold'
                }
            }
        },
        scales: {
            x: {
                grid: {
                    display: block['x_grid_lines'] || true,
                }
            },
            y: {
                beginAtZero: block['y_axis_begin_at_zero'] || true,
                grid: {
                    display: block['y_grid_lines'] || true,
                }
            }
        }
    };
  
      var line_data = {
          type: 'line',
          data: data,
          options: options
      };
  
      return line_data;
  },
  

    get_values_doughnut : function(block){
        var labels = block['x_axis'];
        var colors = this.get_colors(block['x_axis']);
        var backgroundColor = colors[0];
        var borderColors = colors[1];
    
        var data = {
            labels: labels,
            datasets: [{
                label: block['chart_title'] || '',
                data: block['y_axis'],
                backgroundColor: backgroundColor,
                borderColor: "white", // Array of border colors
                borderWidth: 2,
                hoverOffset: block['hover_offset'] || 4
            }]
        };
    
        var options = {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: {
                    display: true,
                    text: block['name'] || 'Pie Chart',
                    font: {
                        weight: 'bold',
                        size:  20 // Set the title font size
                    }
                }
            }
        };
    
        var pie_data = {
            type: 'doughnut',
            data: data,
            options: options
        };
    
        return pie_data;
    },

    get_values_radar : function(block){
        var colors = this.get_colors(block['x_axis']);
        var bgColors = colors[0];
        var borderColors = colors[1];
          var data = {
          labels: block['x_axis'],
          datasets: [{
            label: '',
            data: block['y_axis'],
            fill: true,
            backgroundColor: bgColors,
            borderColor: borderColors,
            pointBackgroundColor: 'rgb(255, 99, 132)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 99, 132)'
          }]
        };
        var options = {
            elements: {
                line: {
                    borderWidth: 1
                }
            },
            plugins: {
                legend: {
                    display: false, // Set to false to hide legend
                    position: block['legend_position'] || 'top',
                    labels: {
                        color: 'rgb(255, 99, 132)' // Customize legend label color
                    }
                },
                title: {
                    display: true,
                    text: block['name'] || 'Pie Chart',
                    font: {
                        weight: 'bold',
                        size:  20 // Set the title font size
                    }
                }
            }
        };
        // radar_data = [data,options]

    var radar_data = {
        type: 'radar',
        data: data,
        options: options
    };

    return radar_data;
    },

    render_dashboards: function() {
        var self = this;
        _.each(this.block_ids, function(block) {
                if (block['type'] == 'tile') {
                    console.log(block.tiles_template)
                    // self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardTile', {widget: block}));
                    self.$('.o_dynamic_dashboard').append(QWeb.render(block.tiles_template, {widget: block}));

                }
                else {
                    self.$('.o_dynamic_chart').append(QWeb.render('DynamicDashboardChart', {widget: block}));
                    var element = $('[data-id=' + block['id'] + ']')
                    
                    var ctx =self.$('.chart_graphs').last()
                    if (!('x_axis' in block)){
                        self._render_dummy_dashboard()
                        
                        return false
                    }
                    var type = block['graph_type']
                    var chart_type = 'self.get_values_' + `${type}(block)`
                    var data = eval(chart_type)
                  var chartCanvas = new Chart(ctx, data);
                  if (chartCanvas) {
                    chartCanvas.height = 500; // Set the desired height, default is 200
                }
                }
        });
    },

    _onClick_block_setting : function(event){
        event.stopPropagation();
        var self = this;
        var id = $(event.currentTarget).closest('.block').attr('data-id');
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'dashboard.block',
            view_mode: 'form',
            res_id: parseInt(id),
            views: [[false,'form']],
            context: {'form_view_initial_mode': 'edit'},
        });
    },

    _onClick_add_block : function(e){
         var self = this;
         var colors = this.get_colors([1,2,3]);
            var bgColors = colors[0];
            var borderColors = colors[1];
         var type = $(e.currentTarget).attr('data-type');
         ajax.jsonRpc('/create/tile', 'call', {
            'type' : type,
            'action_id' : self.action_id
                }).then(function (result) {
                    if(result['type'] == 'tile'){
                        self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardTileStyle_00', {widget: result}));
                    }
                    else{
                        self.$('.o_dynamic_chart').append(QWeb.render('DynamicDashboardChart', {widget: result}));
                        var element = $('[data-id=' + result['id'] + ']')
                        self._render_dummy_dashboard()
                    }
                });
    },
    _render_dummy_dashboard(){
        var self = this;
        var ctx =self.$('.chart_graphs').last()
        var options = {
            type: 'bar',
            data: {
              labels: ['Label1','label2','label3'],
              datasets: [
                  {
                    data: [4,8,2],
                  borderWidth: 1
                  },
                  ]
            },
          }
          var data = {
              labels: ['Label1','label2','label3'],
              datasets: [{
                  label: "Waiting For Setup",
                  data: [4,8,13],
                  fill: true,
                  borderColor: 'rgb(201, 201, 201)', // Line color
                  borderWidth: 1,
                  pointBackgroundColor:  "gray", // Data point color
                  pointBorderColor: "gray",
                  pointBorderWidth: 2,
                  tension: .2
              }]
          };
          var chart = new Chart(ctx, {
              type: 'bar',
              data: data,
              options: {}
          });
    },
    _onClick_view_tile_items:function(e){
        var self = this;
        var domain = [['type', '=', 'tile'],['client_action', '=', self.action_id]];
        
            self.do_action({
                name: 'Tile Items',
                type: 'ir.actions.act_window',
                res_model: 'dashboard.block',
                view_mode: 'tree',
                views: [[false, 'tree']],
                target: 'current',
                domain: domain,
                context: {},  // Add context if needed
            });
    },
    _onClick_view_graph_items:function(e){
        var self = this;
        var domain = [['type', '=', 'graph'],['client_action', '=', self.action_id]];
        
            self.do_action({
                name: 'Tile Items',
                type: 'ir.actions.act_window',
                res_model: 'dashboard.block',
                view_mode: 'tree',
                views: [[false, 'tree']],
                target: 'current',
                domain: domain,
                context: {},  // Add context if needed
            });
    },

    _onClick_tile : function(e){
        e.stopPropagation();
        var self = this;
        var id = $(e.currentTarget).attr('data-id');
        ajax.jsonRpc('/tile/details', 'call', {
           'id': id
        }).then(function (result) {
                self.do_action({
                name : result['model_name'],
                type: 'ir.actions.act_window',
                res_model:result['model'] ,
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: result['filter']
                });
        });
    },



});


core.action_registry.add('dynamic_dashboard', DynamicDashboard);

return DynamicDashboard;

});
