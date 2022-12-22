import { Component, OnInit, EventEmitter, Input, OnDestroy, Output, TemplateRef } from '@angular/core';
import { NbDialogService } from '@nebular/theme';

import * as L from 'leaflet';

import { InstagramMapService } from './instagram-map.service';
import { NbThemeService } from '@nebular/theme';
import { combineLatest } from 'rxjs';
import { takeWhile } from 'rxjs/operators';


@Component({
    selector: 'ngx-instagram-map',
    templateUrl: './instagram-map.component.html',
    styleUrls: ['./instagram-map.component.scss']
})
export class InstagramMapComponent implements OnDestroy {

    @Input() private data: any;
    @Output() select: EventEmitter<any> = new EventEmitter();

    private validation: any;
    private instagramMaps: any;
  
    layers = [];
    currentTheme: any;
    alive = true;
    selectedCountry;
  
    options = {
        zoom: 2,
        minZoom: 1,
        maxZoom: 8,
        zoomControl: false,
        center: L.latLng({lat: 38.991709, lng: -76.886109}),
        maxBounds: new L.LatLngBounds(
          new L.LatLng(-89.98155760646617, -180),
          new L.LatLng(90.99346179538875, 180),
        ),
        // maxBoundsViscosity: 1.0,
        maxBoundsViscosity: 0.5,
    };

    constructor(private ecMapService: InstagramMapService,
                private theme: NbThemeService, 
                private dialogService: NbDialogService) {
        combineLatest([
            this.ecMapService.getCords(),
            this.theme.getJsTheme(),
        ])
            .pipe(takeWhile(() => this.alive))
            .subscribe(([cords, config]: [any, any]) => {
              this.currentTheme = config.variables.countryOrders;
              this.layers = [this.createGeoJsonLayer(cords)];
            });
    }

    ngOnInit() {
        console.log("Instagram Map Component");
        this.instagramMaps = this.data.result[4].graphic[2].postsloc;
        this.validation = this.data.result[2].validation;
        console.log("Data: ", this.instagramMaps)
    }

    // openDialog(dialog: TemplateRef<any>) {
    //     this.dialogService.open(dialog);
    // }

    mapReady(map: L.Map) {
        map.addControl(L.control.zoom({position: 'bottomright'}));
    
        // fix the map fully displaying, existing leaflet bag
        setTimeout(() => {
            map.invalidateSize();
        }, 0);
    
        // Icon
        var greenIcon = L.icon({
            iconUrl: './assets/images/map-marker-icon-default.png',
            // shadowUrl: 'leaf-shadow.png',
        
            iconSize:     [38, 38], // size of the icon
            // shadowSize:   [50, 64], // size of the shadow
            // iconAnchor:   [22, 94], // point of the icon which will correspond to marker's location
            // shadowAnchor: [4, 62],  // the same for the shadow
            popupAnchor:  [0, -6] // point from which the popup should open relative to the iconAnchor
        });
        // Points
        for (let loc in this.instagramMaps) {
            console.warn("LOCCCCCCCCC", this.instagramMaps[loc])
            if (this.instagramMaps[loc]['Latitude'] != "None") {
                L.marker([this.instagramMaps[loc]['Latitude'], this.instagramMaps[loc]['Longitude']], {icon: greenIcon}).addTo(map).bindPopup("<b>" + this.instagramMaps[loc]['Name'] + "</b><br>Caption : " + this.instagramMaps[loc]['Caption'] + "<br>Time : " + this.instagramMaps[loc]['Time'] + "<br>Accessability : " + this.instagramMaps[loc]['Accessability']);
            }
        }
        // L.marker([, ], {icon: greenIcon}).addTo(map).bindPopup("<b>" + this.instagramMaps[loc]['Name'] + "</b><br>Caption : " + this.instagramMaps[loc]['Caption']);
          // L.marker([0, 0], {icon: greenIcon}).addTo(map).bindPopup("Esto es el 0 0");
          // var marker = L.marker([51.5, -0.09]).addTo(map);
          // marker.bindPopup("<b>Hello world!</b><br>I am a popup.").openPopup();
    }
  
    private createGeoJsonLayer(cords) {
      return L.geoJSON(
        cords as any,
        {
          style: () => ({
              // weight: this.currentTheme.countryBorderWidth,
            weight: 2,
              // fillColor: this.currentTheme.countryFillColor,
            fillColor: "black",
            fillOpacity: 0.3,
              // color: this.currentTheme.countryBorderColor,
            color: "black",
            opacity: 0.8,
          }),
          onEachFeature: (f, l) => {
            this.onEachFeature(f, l);
          },
        });
    }
  
    private onEachFeature(feature, layer) {
      layer.on({
        mouseover: (e) => this.highlightFeature(e.target),
        mouseout: (e) => this.moveout(e.target),
        click: (e) => this.selectFeature(e.target),
      });
    }
  
    private highlightFeature(featureLayer) {
      if (featureLayer) {
        featureLayer.setStyle({
            //         weight: this.currentTheme.hoveredCountryBorderWidth,
            //         fillColor: this.currentTheme.hoveredCountryFillColor,
            //         color: this.currentTheme.hoveredCountryBorderColor,
          weight: 2,
          fillColor: "#00f9a6",
          fillOpacity: 0.2,
          color: "#00f9a6",
        });
  
        if (!L.Browser.ie && !L.Browser.opera12 && !L.Browser.edge) {
          featureLayer.bringToFront();
        }
      }
    }
  
    private moveout(featureLayer) {
      if (featureLayer !== this.selectedCountry) {
        this.resetHighlight(featureLayer);
  
        // When countries have common border we should highlight selected country once again
        this.highlightFeature(this.selectedCountry);
      }
    }
  
    private resetHighlight(featureLayer) {
      if (featureLayer) {
        const geoJsonLayer = this.layers[0];
  
        geoJsonLayer.resetStyle(featureLayer);
      }
    }
  
    private selectFeature(featureLayer) {
      if (featureLayer !== this.selectedCountry) {
        this.resetHighlight(this.selectedCountry);
        this.highlightFeature(featureLayer);
        this.selectedCountry = featureLayer;
        this.select.emit(featureLayer.feature.properties.name);
      }
    }
  
    private findFeatureLayerByCountryId(id) {
      const layers = this.layers[0].getLayers();
      const featureLayer = layers.find(item => {
        return item.feature.id === id;
      });
  
      return featureLayer ? featureLayer : null;
    }
  
    ngOnDestroy(): void {
      this.alive = false;
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
