odoo.define('mnc_fuel_management.GraphRenderer', function (require) {
    'use strict';

    var GraphRenderer = require('web.GraphRenderer');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');

    var data_y = []

    rpc.query({
        model: 'fuel.distribution.line',
        method: 'get_data_high',

    }).then(function (data) {
        data_y = data
    });


    GraphRenderer.include({
        _render: function () {
            this._super.apply(this, arguments);

            var self = this;
            var newList = [];
            if (self.chart) {
                let labels = self.chart.config.data.labels
                for (let i = 0; i < labels.length; i++) {
                    // Tambahkan elemen ke newList
                    newList.push(labels[i][0]);
                    }            
            }
            // Menunggu hingga elemen kanvas siap
            this.$el.ready(function() {
                // Memeriksa apakah data tersedia dan field target ada di dalam state
                var target = 10000;
                if (self.state && self.state.dataPoints && self.state.dataPoints.length > 0 && data_y.length > 0) {
                    // var target = self.state.data[0].target; // Asumsi target sama untuk semua data

                    // Mendapatkan konteks kanvas
                    var canvas = self.$el.find('canvas')[0];
                    if (canvas) {
                        var ctx = canvas.getContext('2d');
                        var charts = []

                        var targetLine = {
                            id: 'targetLine',
                            beforeDraw: function (chart) {
                                var yScale = chart.scales['y-axis-0'];
                                var yValue = yScale.getPixelForValue(0);

                                ctx.save();
                                ctx.beginPath();
                                ctx.moveTo(chart.chartArea.left, yValue);
                                ctx.lineTo(chart.chartArea.right, yValue);
                                ctx.lineWidth = 2;
                                ctx.strokeStyle = 'red';
                                ctx.moveTo(chart.chartArea.left, yValue);

                                var axis_x = chart.scales['x-axis-0']._gridLineItems;
                                if (axis_x){
                                    var y = axis_x[0]['ty1']
                                    for (let i=0; i<axis_x.length; i++){
                                        target = y - data_y[i]['high']
                                        yValue = yScale.getPixelForValue(target)
                                        charts.push([axis_x[i]['tx1'],target])
                                    }
                                    // charts.push([chart.chartArea.right, yValue])
                                }
                                charts.sort(function(a,b) {
                                    return a[0]-b[0]
                                });

                                var temp = ''
                                var unique = charts.sort().filter(r => {
                                    if (r.join("") !== temp) {
                                      temp = r.join("")
                                      return true
                                    }
                                  })
                                unique.sort(function(a,b) {
                                    return a[0]-b[0]
                                });

                                if (unique.length > 0){
                                    for (let i=0; i<unique.length;i++){
                                        // console.log("\n\n looping", charts[i][0], chart.chartArea.right)
                                        // yValue = yScale.getPixelForValue(unique[i][1]);
                                        ctx.lineTo(unique[i][0], unique[i][1]);
                                        if (unique[i][0] == chart.chartArea.right){
                                            break;
                                        }
                                    }
                                    ctx.stroke();
                                    ctx.restore();
                                }
                            }
                        };
                        if (!Chart.plugins.getAll().find(plugin => plugin.id === 'targetLine')) {
                            Chart.plugins.register(targetLine);
                        }
                        Chart.plugins.register(targetLine);
                        // Lanjutkan kode di sini jika canvas ada
                    } else {
                        console.error('Canvas element not found');
                        // Tambahkan tindakan lain jika canvas tidak ditemukan
                    }

                    if (self.chart) {
                        self.chart.update();
                    }
                } else {
                    console.warn("Data tidak tersedia dalam state.");
                }
            });
        },
    });
});
