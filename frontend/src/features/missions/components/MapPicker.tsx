import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet's default icon path issues in React
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

const customIcon = new L.DivIcon({
  className: "bg-transparent",
  html: `
    <div class="relative flex items-center justify-center w-6 h-6 -ml-3 -mt-3">
      <div class="absolute inset-0 rounded-full bg-[#C8A24A] opacity-20 animate-ping"></div>
      <div class="w-3 h-3 rounded-full bg-[#C8A24A] shadow-[0_0_12px_rgba(200,162,74,0.8)] border border-[#0B0F14]"></div>
    </div>
  `,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

interface MapPickerProps {
  lat: string;
  lng: string;
  onChange: (lat: string, lng: string) => void;
}

function LocationMarker({ position, setPosition }: { position: L.LatLng | null; setPosition: (pos: L.LatLng) => void }) {
  useMapEvents({
    click(e) {
      setPosition(e.latlng);
    },
  });

  return position === null ? null : <Marker position={position} icon={customIcon}></Marker>;
}

function MapUpdater({ position }: { position: L.LatLng | null }) {
  const map = useMap();
  useEffect(() => {
    if (position) {
      map.setView(position, map.getZoom(), { animate: true });
    }
  }, [position, map]);
  return null;
}

export function MapPicker({ lat, lng, onChange }: MapPickerProps) {
  const [position, setPosition] = useState<L.LatLng | null>(null);

  // Initialize position from props
  useEffect(() => {
    const parsedLat = parseFloat(lat);
    const parsedLng = parseFloat(lng);
    if (!isNaN(parsedLat) && !isNaN(parsedLng)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPosition(new L.LatLng(parsedLat, parsedLng));
    }
  }, [lat, lng]);

  function handlePositionChange(pos: L.LatLng) {
    setPosition(pos);
    onChange(pos.lat.toFixed(6), pos.lng.toFixed(6));
  }

  const defaultCenter: [number, number] = [parseFloat(lat) || 48.3794, parseFloat(lng) || 31.1656]; // Ukraine center if empty

  return (
    <div
      className="relative rounded-xl overflow-hidden group"
      style={{
        height: "200px",
        background: "#0F1621",
        border: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <style>{`
        .leaflet-bar a, .leaflet-bar a:hover {
          background-color: #1A2230 !important;
          color: #E6EAF0 !important;
          border-bottom: 1px solid rgba(255,255,255,0.1) !important;
        }
        .leaflet-bar {
          border: 1px solid rgba(255,255,255,0.1) !important;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
        }
        .leaflet-bar a.leaflet-disabled {
          color: #4B5563 !important;
          background-color: #1A2230 !important;
        }
      `}</style>
      <MapContainer
        center={position ? [position.lat, position.lng] : defaultCenter}
        zoom={5}
        style={{ height: "100%", width: "100%", zIndex: 0 }}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <LocationMarker position={position} setPosition={handlePositionChange} />
        <MapUpdater position={position} />
      </MapContainer>
      <div className="absolute top-3 right-3 text-[10px] font-mono px-2 py-1 rounded bg-black/60 text-[#8A94A6] pointer-events-none z-10 transition-opacity opacity-70 group-hover:opacity-100">
        Click to set position
      </div>
      {position && (
        <div className="absolute bottom-3 left-3 text-[10px] font-mono px-2 py-1 rounded bg-black/80 text-[#C8A24A] pointer-events-none z-10 shadow-lg border border-white/5">
          {position.lat.toFixed(4)}° N · {position.lng.toFixed(4)}° E
        </div>
      )}
    </div>
  );
}
