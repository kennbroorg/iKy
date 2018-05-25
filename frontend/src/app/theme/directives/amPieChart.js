/**
 * Created by kennbro on 16/04/18.
 */

(function () {
    'use strict';

    angular.module('BlurAdmin.theme')
      .directive( 'amPieChart', amPieChart);
    
    /** @ngInject */
    function amPieChart(layoutPaths, baConfig) {
        return {
          restrict: 'E',
          scope: {
            values: '=values',
            chartid: '@'
          },
          //replace:true,
          // template: '<div id="item-1" style="min-width: 310px; height: 400px; margin: 0 auto"></div>',
          //template: '<div id={{::uniqueId}} style="min-width: 310px; height: 400px; margin: 0 auto"></div>',

          link: function (scope, element) {

            var divId = scope.chartid

            var layoutColors = baConfig.colors;

            var chart = false;

            var initChart = function() {
                  // if (chart) chart.destroy();
                  var config = scope.config || {};
                   chart = AmCharts.makeChart(divId, {



                      type: 'pie',
                      startDuration: 0,
                      theme: 'blur',
                      addClassNames: true,
                      color: layoutColors.defaultText,
                      labelTickColor: layoutColors.borderDark,
                      baseColor: '#209E91',
                      legend: {
                        enabled: false
                      },
                      innerRadius: '40%',
                      radius: 110,
                      defs: {
                        filter: [
                          {
                            id: 'shadow',
                            width: '200%',
                            height: '200%',
                            feOffset: {
                              result: 'offOut',
                              in: 'SourceAlpha',
                              dx: 0,
                              dy: 0
                            },
                            feGaussianBlur: {
                              result: 'blurOut',
                              in: 'offOut',
                              stdDeviation: 5
                            },
                            feBlend: {
                              in: 'SourceGraphic',
                              in2: 'blurOut',
                              mode: 'normal'
                            }
                          }
                        ]
                      },
                      dataProvider: scope.values,
                      // dataProvider: [
                      //   {
                      //     title: 'Followers',
                      //     value: 501.9
                      //   },
                      //   {
                      //     title: 'Following',
                      //     value: 301.9
                      //   },
                      //   {
                      //     title: 'Listed',
                      //     value: 201.1
                      //   }
                      // ],
                      valueField: 'value',
                      titleField: 'title',
                      export: {
                        enabled: true
                      },
                      creditsPosition: 'bottom-left',

                      maxLabelWidth: 50,
                      autoMargins: false,
                      marginTop: 0,
                      alpha: 0.3,
                      outlineAlpha: 0.3,
                      // borderAlpha: 1,
                      // backgroundAlpha: 0.3,
                      marginBottom: 0,
                      marginLeft: 0,
                      marginRight: 0,
                      pullOutRadius: 0,
                      pathToImages: layoutPaths.images.amChart,
                      // responsive: {
                        // enabled: true
                        // rules: [
                        //   // at 900px wide, we hide legend
                        //   {
                        //     maxWidth: 900,
                        //     overrides: {
                        //       legend: {
                        //         enabled: false
                        //       }
                        //     }
                        //   },

                        //   // at 200 px we hide value axis labels altogether
                        //   {
                        //     maxWidth: 200,
                        //     overrides: {
                        //       valueAxes: {
                        //         labelsEnabled: false
                        //       },
                        //       marginTop: 0,
                        //       marginBottom: 0,
                        //       marginLeft: 0,
                        //       marginRight: 0
                        //     }
                        //   }
                        // ]
                      // }


                  });

                chart.addListener('init', handleInit);

                chart.addListener('rollOverSlice', function (e) {
                  handleRollOver(e);
                });

                function handleInit() {
                  chart.legend.addListener('rollOverItem', handleRollOver);
                }

                function handleRollOver(e) {
                  var wedge = e.dataItem.wedge.node;
                  wedge.parentNode.appendChild(wedge);
                }
            };


            scope.$watch('values', function(){
              // scope.render(scope.values);
              initChart();
            });

          }
        };
      }

}());
