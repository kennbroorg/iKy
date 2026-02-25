import { useEffect } from "react";

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";

/**
 * Fix Leaflet default marker icons in bundled environments.
 * The default icon paths point to missing files when using Vite/webpack.
 */
const cyanIcon = new L.Icon({
  iconUrl:
    "data:image/svg+xml;base64," +
    btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="25" height="41" viewBox="0 0 25 41">
      <path d="M12.5 0C5.6 0 0 5.6 0 12.5C0 22 12.5 41 12.5 41S25 22 25 12.5C25 5.6 19.4 0 12.5 0z" fill="#06b6d4"/>
      <circle cx="12.5" cy="12.5" r="5" fill="#0e7490" opacity="0.6"/>
      <circle cx="12.5" cy="12.5" r="3" fill="white" opacity="0.8"/>
    </svg>`),
  iconSize: [25, 41],
  iconAnchor: [12.5, 41],
  popupAnchor: [0, -41],
});

interface LocationMapProps {
  locations: { lat: number; lng: number; label: string }[];
  height?: string;
}

/** Helper component to auto-fit map bounds to all markers. */
function FitBounds({
  locations,
}: {
  locations: { lat: number; lng: number }[];
}) {
  const map = useMap();

  useEffect(() => {
    if (locations.length === 0) return;

    if (locations.length === 1) {
      map.setView([locations[0].lat, locations[0].lng], 10);
      return;
    }

    const bounds = L.latLngBounds(
      locations.map((loc) => [loc.lat, loc.lng] as L.LatLngTuple),
    );
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [map, locations]);

  return null;
}

/**
 * Location map component using Leaflet with dark CartoDB tiles
 * and cyan-colored markers.
 */
export function LocationMap({
  locations,
  height = "400px",
}: LocationMapProps) {
  if (!locations || locations.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">
        No location data available.
      </p>
    );
  }

  const center: L.LatLngTuple =
    locations.length === 1
      ? [locations[0].lat, locations[0].lng]
      : [0, 0];

  return (
    <div
      className="overflow-hidden rounded-md border border-border"
      style={{ height }}
    >
      <MapContainer
        center={center}
        zoom={3}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%" }}
        attributionControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {locations.map((loc, i) => (
          <Marker
            key={`${loc.lat}-${loc.lng}-${i}`}
            position={[loc.lat, loc.lng]}
            icon={cyanIcon}
          >
            <Popup>
              <span className="text-sm font-medium">{loc.label}</span>
            </Popup>
          </Marker>
        ))}
        <FitBounds locations={locations} />
      </MapContainer>
    </div>
  );
}
