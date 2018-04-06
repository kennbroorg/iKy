/**
 * Created by kennbro on 13/04/18.
 */

(function () {
    'use strict';

    angular.module('BlurAdmin.theme')
      .directive( 'textcloud', textcloud);
    
    /** @ngInject */
    function textcloud() {
        return {
          restrict: 'E',
          scope: {
            words: '=words'
          },

          link: function (scope, element) {

                var w = element.parent()[0].offsetWidth;
                var h = element.parent()[0].offsetHeight;

                function SVG3DTagCloud( element, params ) {

                    var settings = {
                        entries: [],
                        width: '100%',
                        height: '100%',
                        radius: '70%',
                        radiusMin: 75,
                        bgDraw: true,
                        bgColor: '#000',
                        bgOpacity: 0.01,
                        opacityOver: 1.00,
                        opacityOut: 0.05,
                        opacitySpeed: 6,
                        fov: 800,
                        speed: 3,
                        fontFamily: 'Arial, sans-serif',
                        fontSize: '15',
                        fontColor: '#fff',
                        fontWeight: 'normal',//bold
                        fontStyle: 'normal',//italic 
                        fontStretch: 'normal',//wider, narrower, ultra-condensed, extra-condensed, condensed, semi-condensed, semi-expanded, expanded, extra-expanded, ultra-expanded
                        fontToUpperCase: false,
                        tooltipFontFamily: 'Arial, sans-serif',
                        tooltipFontSize: '15',
                        tooltipFontColor: '#fff',
                        tooltipFontWeight: 'normal',//bold
                        tooltipFontStyle: 'normal',//italic 
                        tooltipFontStretch: 'normal',//wider, narrower, ultra-condensed, extra-condensed, condensed, semi-condensed, semi-expanded, expanded, extra-expanded, ultra-expanded
                        tooltipFontToUpperCase: false,
                        tooltipTextAnchor: 'left',
                        tooltipDiffX: 0,
                        tooltipDiffY: 10
                    };
                        
                    if ( params !== undefined )
                        for ( var prop in params )
                            if ( params.hasOwnProperty( prop ) && settings.hasOwnProperty( prop ) )
                                settings[ prop ] = params[ prop ];

                    if ( !settings.entries.length )
                        return false;

                    var entryHolder = [];
                    var tooltip;
                    var radius;
                    var diameter;
                    var mouseReact = true;
                    var mousePos = { x: 0, y: 0 };
                    var center2D;
                    var center3D = { x: 0, y: 0, z: 0 };
                    var speed = { x: 0, y: 0 };
                    var position = { sx: 0, cx: 0, sy: 0, cy: 0 };
                    var MATHPI180 = Math.PI / 180;
                    var svg;
                    var svgNS = 'http://www.w3.org/2000/svg';
                    var bg;

                    function init() {
                        svg = document.createElementNS( svgNS, 'svg' );
                        svg.addEventListener( 'mousemove', mouseMoveHandler );
                        element.appendChild( svg );

                        if ( settings.bgDraw ) {
                            bg = document.createElementNS( svgNS, 'rect' );
                            bg.setAttribute( 'x', 0 );
                            bg.setAttribute( 'y', 0 );
                            bg.setAttribute( 'fill', settings.bgColor );
                            bg.setAttribute( 'fill-opacity', settings.bgOpacity );
                            svg.appendChild( bg );
                        }

                        addEntries();
                        reInit();
                        animloop();
                        window.addEventListener( 'resize', resizeHandler ); /* This probably don't work */
                    };

                    function reInit() {
                        var windowWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
                        var windowHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
                        var svgWidth = windowWidth;
                        var svgHeight = windowHeight;

                        if ( settings.width.toString().indexOf( '%' ) > 0 || settings.height.toString().indexOf( '%' ) > 0 ) {
                            svgWidth = Math.round( w / 100 * parseInt( settings.width ) );
                            svgHeight = Math.round( svgWidth / 100 * parseInt( settings.height ) );
                        } else {
                            svgWidth = parseInt( settings.width );
                            svgHeight = parseInt( settings.height );
                        }

                        if ( windowWidth <= svgWidth )
                            svgWidth = windowWidth;

                        if ( windowHeight <= svgHeight )
                            svgHeight = windowHeight;

                        center2D = { x: svgWidth / 2, y: svgHeight / 2 };

                        speed.x = settings.speed / center2D.x;
                        speed.y = settings.speed / center2D.y;

                        if ( svgWidth >= svgHeight )
                            diameter = svgHeight / 100 * parseInt( settings.radius );
                        else
                            diameter = svgWidth / 100 * parseInt( settings.radius );

                        if ( diameter < 1 )
                            diameter = 1;

                        radius = diameter / 2;

                        if ( radius < settings.radiusMin ) {

                            radius = settings.radiusMin;
                            diameter = radius * 2;

                        }

                        //---

                        svg.setAttribute( 'width', svgWidth );
                        svg.setAttribute( 'height', svgHeight );

                        if ( settings.bgDraw ) {

                            bg.setAttribute( 'width', svgWidth );
                            bg.setAttribute( 'height', svgHeight );

                        }

                        //---

                        setEntryPositions( radius );

                    };

                    //---

                    function setEntryPositions( radius ) {

                        for ( var i = 0, l = entryHolder.length; i < l; i++ ) {

                            setEntryPosition( entryHolder[ i ], radius );

                        }

                    };

                    function setEntryPosition( entry, radius ) {

                        var dx = entry.vectorPosition.x - center3D.x;
                        var dy = entry.vectorPosition.y - center3D.y;
                        var dz = entry.vectorPosition.z - center3D.z;

                        var length = Math.sqrt( dx * dx + dy * dy + dz * dz );

                        entry.vectorPosition.x /= length;
                        entry.vectorPosition.y /= length;
                        entry.vectorPosition.z /= length;

                        entry.vectorPosition.x *= radius;
                        entry.vectorPosition.y *= radius;
                        entry.vectorPosition.z *= radius;

                    };

                    function addEntry( index, entryObj, x, y, z ) {
                        
                        var entry = {};

                            if ( typeof entryObj.label != 'undefined' ) {

                                entry.element = document.createElementNS( svgNS, 'text' );
                                entry.element.setAttribute( 'x', 0 );
                                entry.element.setAttribute( 'y', 0 );
                                entry.element.setAttribute( 'fill', settings.fontColor );
                                entry.element.setAttribute( 'font-family', settings.fontFamily );
                                entry.element.setAttribute( 'font-size', settings.fontSize );
                                entry.element.setAttribute( 'font-weight', settings.fontWeight );
                                entry.element.setAttribute( 'font-style', settings.fontStyle );
                                entry.element.setAttribute( 'font-stretch', settings.fontStretch );
                                entry.element.setAttribute( 'text-anchor', 'middle' );
                                entry.element.textContent = settings.fontToUpperCase ? entryObj.label.toUpperCase() : entryObj.label;

                            } else if ( typeof entryObj.image != 'undefined' ) {

                                entry.element = document.createElementNS( svgNS, 'image' );
                                entry.element.setAttribute( 'x', 0 );
                                entry.element.setAttribute( 'y', 0 );
                                entry.element.setAttribute( 'width', entryObj.width );
                                entry.element.setAttribute( 'height', entryObj.height );
                                entry.element.setAttribute( 'id', 'image_' + index );
                                entry.element.setAttributeNS( 'http://www.w3.org/1999/xlink','href', entryObj.image );

                                entry.diffX = entryObj.width / 2;
                                entry.diffY = entryObj.height / 2;
                                
                            }

                            entry.link = document.createElementNS( svgNS, 'a' );
                            entry.link.setAttributeNS( 'http://www.w3.org/1999/xlink', 'xlink:href', entryObj.url );
                            entry.link.setAttribute( 'target', entryObj.target );
                            entry.link.addEventListener( 'mouseover', mouseOverHandler, true );
                            entry.link.addEventListener( 'mouseout', mouseOutHandler, true );
                            entry.link.appendChild( entry.element );

                            if ( typeof entryObj.tooltip != 'undefined' ) {

                                entry.tooltip = true;
                                entry.tooltipLabel = settings.tooltipFontToUpperCase ? entryObj.tooltip.toUpperCase() : entryObj.tooltip;;

                            } else {

                                entry.tooltip = false;

                            }

                            entry.index = index;
                            entry.mouseOver = false;

                            entry.vectorPosition = { x:x, y:y, z:z };
                            entry.vector2D = { x:0, y:0 };

                        svg.appendChild( entry.link );
                            
                        return entry;
                    
                    };

                    function addEntries() {

                        var tooltip = false;

                        for ( var i = 1, l = settings.entries.length + 1; i < l; i++ ) {

                            var phi = Math.acos( -1 + ( 2 * i ) / l );
                            var theta = Math.sqrt( l * Math.PI ) * phi;

                            var x = Math.cos( theta ) * Math.sin( phi );
                            var y = Math.sin( theta ) * Math.sin( phi );
                            var z = Math.cos( phi );

                            var entry = addEntry( i - 1, settings.entries[ i - 1 ], x, y, z );
                            
                            entryHolder.push( entry );

                            if ( typeof settings.entries[ i - 1 ].tooltip != 'undefined' ) {

                                tooltip = true;

                            }
                        
                        }

                        if ( tooltip ) {

                            addTooltip();

                        }
                    
                    };

                    function addTooltip() {

                        tooltip = document.createElementNS( svgNS, 'text' );
                        tooltip.setAttribute( 'x', 0 );
                        tooltip.setAttribute( 'y', 0 );
                        tooltip.setAttribute( 'fill', settings.tooltipFontColor );
                        tooltip.setAttribute( 'font-family', settings.tooltipFontFamily );
                        tooltip.setAttribute( 'font-size', settings.tooltipFontSize );
                        tooltip.setAttribute( 'font-weight', settings.tooltipFontWeight );
                        tooltip.setAttribute( 'font-style', settings.tooltipFontStyle );
                        tooltip.setAttribute( 'font-stretch', settings.tooltipFontStretch );
                        tooltip.setAttribute( 'text-anchor', settings.tooltipTextAnchor );
                        tooltip.textContent = '';

                        svg.appendChild( tooltip );

                    };

                    function getEntryByElement( element ) {

                        for ( var i = 0, l = entryHolder.length; i < l; i++ ) {

                            var entry = entryHolder[ i ];

                            if ( entry.element.getAttribute( 'x' ) === element.getAttribute( 'x' ) && 
                                 entry.element.getAttribute( 'y' ) === element.getAttribute( 'y' ) ) {

                                return entry;

                            }

                        }

                        return;

                    };

                    function highlightEntry( entry ) {

                        for ( var i = 0, l = entryHolder.length; i < l; i++ ) {

                            var e = entryHolder[ i ];

                            if ( e.index === entry.index ) {

                                e.mouseOver = true; 

                            } else {

                                e.mouseOver = false; 

                            }

                        } 

                    };

                    //---

                    function showTooltip( entry ) {

                        if ( entry.tooltip ) {

                            tooltip.setAttribute( 'x', entry.vector2D.x - settings.tooltipDiffX );
                            tooltip.setAttribute( 'y', entry.vector2D.y - settings.tooltipDiffY );

                            tooltip.textContent = settings.tooltipFontToUpperCase ? entry.tooltipLabel.toUpperCase() : entry.tooltipLabel;

                            tooltip.setAttribute( 'opacity', 1.0 );

                        }

                    };

                    function hideTooltip( entry ) {

                        tooltip.setAttribute( 'opacity', 0.0 );

                    };

                    //---
                        
                    function render() {

                        var fx = speed.x * mousePos.x - settings.speed;
                        var fy = settings.speed - speed.y * mousePos.y;
                        
                        var angleX = fx * MATHPI180;
                        var angleY = fy * MATHPI180;

                        position.sx = Math.sin( angleX );
                        position.cx = Math.cos( angleX );
                        position.sy = Math.sin( angleY );
                        position.cy = Math.cos( angleY );

                        //---

                        for ( var i = 0, l = entryHolder.length; i < l; i++ ) {
                
                            var entry = entryHolder[ i ];

                            //---

                            if ( mouseReact ) {

                                var rx = entry.vectorPosition.x;
                                var rz = entry.vectorPosition.y * position.sy + entry.vectorPosition.z * position.cy;

                                entry.vectorPosition.x = rx * position.cx + rz * position.sx;
                                entry.vectorPosition.y = entry.vectorPosition.y * position.cy + entry.vectorPosition.z * -position.sy;
                                entry.vectorPosition.z = rx * -position.sx + rz * position.cx;

                            }

                            //---

                            var scale = settings.fov / ( settings.fov + entry.vectorPosition.z );

                            entry.vector2D.x = entry.vectorPosition.x * scale + center2D.x; 
                            entry.vector2D.y = entry.vectorPosition.y * scale + center2D.y;
                            
                            //---

                            if ( entry.diffX && entry.diffY ) {

                                entry.vector2D.x -= entry.diffX;
                                entry.vector2D.y -= entry.diffY;

                            }

                            //---

                            entry.element.setAttribute( 'x', entry.vector2D.x );
                            entry.element.setAttribute( 'y', entry.vector2D.y );

                            //---

                            var opacity;

                            if ( mouseReact ) {

                                opacity = ( radius - entry.vectorPosition.z ) / diameter;

                                if ( opacity < settings.opacityOut ) {

                                    opacity = settings.opacityOut;

                                }

                            } else {

                                opacity = parseFloat( entry.element.getAttribute( 'opacity' ) );

                                if ( entry.mouseOver ) {

                                    opacity += ( settings.opacityOver - opacity ) / settings.opacitySpeed;

                                } else {

                                    opacity += ( settings.opacityOut - opacity ) / settings.opacitySpeed;

                                }

                            }

                            entry.element.setAttribute( 'opacity', opacity );
                            
                        }

                        //---

                        entryHolder = entryHolder.sort( function( a, b ) {

                            return ( b.vectorPosition.z - a.vectorPosition.z );

                        } );

                    };

                    //---

                    window.requestAnimFrame = ( function() {

                        return  window.requestAnimationFrame       ||
                                window.webkitRequestAnimationFrame ||
                                window.mozRequestAnimationFrame    ||
                                function( callback ) {
                                    window.setTimeout( callback, 1000 / 60 );
                                };

                    } )();
                        
                    function animloop() {

                        requestAnimFrame( animloop );

                        render();

                    };

                    //---

                    function mouseOverHandler( event ) {

                        mouseReact = false;

                        //---

                        var entry = getEntryByElement( event.target );

                        highlightEntry( entry );

                        if ( entry.tooltip ) {

                            showTooltip( entry );

                        }

                    };

                    function mouseOutHandler( event ) {

                        mouseReact = true;

                        //---

                        var entry = getEntryByElement( event.target );

                        if ( entry.tooltip ) {

                            hideTooltip( entry );

                        }

                    };

                    //---

                    function mouseMoveHandler( event ) {

                        mousePos = getMousePos( svg, event );

                    };

                    function getMousePos( svg, event ) {

                        var rect = svg.getBoundingClientRect();

                        return { 

                            x: event.clientX - rect.left, 
                            y: event.clientY - rect.top 

                        };

                    };

                    //---

                    function resizeHandler( event ) {

                        reInit();

                    };
                    
                    //---

                    init();
             
                };

              scope.$watch('words', function(){
                var settings = {
                    entries: scope.words,
                    width: '90%',
                    height: '70%',
                    radius: '75%',
                    radiusMin: 75,
                    bgDraw: true,
                    bgColor: '#111',
                    opacityOver: 1.00,
                    opacityOut: 0.05,
                    opacitySpeed: 6,
                    fov: 800,
                    speed: .2,
                    fontFamily: 'Oswald, Arial, sans-serif',
                    fontSize: '15',
                    fontColor: '#fff',
                    fontWeight: 'normal',//bold
                    fontStyle: 'normal',//italic 
                    fontStretch: 'normal',//wider, narrower, ultra-condensed, extra-condensed, condensed, semi-condensed, semi-expanded, expanded, extra-expanded, ultra-expanded
                    fontToUpperCase: true
                };

                var el = element[0];
                while (el.firstChild) {
                    el.removeChild(el.firstChild);
                }
                var svg3DTagCloud = new SVG3DTagCloud( el, settings );

              });

          }
        };
      }

}());
