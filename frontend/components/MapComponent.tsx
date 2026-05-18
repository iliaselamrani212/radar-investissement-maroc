"use client";

import { CircleMarker, GeoJSON, MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix Leaflet default icon broken by webpack/Next.js bundler
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const sectorIcon = (secteur: string) => {
  const colors: Record<string, string> = {
    Industrie: "#e63946",
    Énergie: "#f4a261",
    Agriculture: "#2a9d8f",
    Tourisme: "#457b9d",
    Tech: "#6a4c93",
    Immobilier: "#c77dff",
    Logistique: "#8d8d8d",
    Infrastructure: "#4361ee",
    default: "#2D6A4F",
  };
  const color = colors[secteur] ?? colors.default;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="24" height="36">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 7.2 12 24 12 24S24 19.2 24 12C24 5.4 18.6 0 12 0z" fill="${color}" stroke="white" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="white"/>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
  });
};

const formatMAD = (amount: number | null | undefined) => {
  if (!amount) return "N/A";
  if (amount >= 1e9) return `${(amount / 1e9).toFixed(1)} Mds MAD`;
  if (amount >= 1e6) return `${(amount / 1e6).toFixed(0)} M MAD`;
  return `${amount.toLocaleString("fr-MA")} MAD`;
};

export interface ProjectMarker {
  id: string;
  titre: string;
  latitude: number;
  longitude: number;
  montant_mad?: number | null;
  secteur?: string;
  region?: string | null;
  stade?: string | null;
  score_fiabilite?: number | null;
}

export interface RegionCenter {
  nom: string;
  latitude: number;
  longitude: number;
}

interface MapComponentProps {
  projects: ProjectMarker[];
  regions: RegionCenter[];
  sectorFilter?: string;
}

const REGION_BOUNDS: Record<string, [[number, number], [number, number]]> = {
  "Tanger-TÃ©touan-Al HoceÃ¯ma": [[35.0, -6.3], [35.95, -3.8]],
  "Oriental": [[32.0, -3.2], [35.1, -0.9]],
  "FÃ¨s-MeknÃ¨s": [[33.0, -6.0], [34.7, -3.9]],
  "Rabat-SalÃ©-KÃ©nitra": [[33.5, -7.2], [34.7, -5.7]],
  "Casablanca-Settat": [[32.2, -8.9], [33.9, -6.7]],
  "BÃ©ni Mellal-KhÃ©nifra": [[31.8, -7.1], [33.3, -5.0]],
  "Marrakech-Safi": [[30.8, -9.9], [32.4, -6.8]],
  "Souss-Massa": [[29.2, -10.3], [31.1, -8.0]],
  "DrÃ¢a-Tafilalet": [[30.1, -7.2], [32.5, -3.7]],
  "Guelmim-Oued Noun": [[27.7, -11.4], [29.6, -8.7]],
  "LaÃ¢youne-Sakia El Hamra": [[25.8, -14.7], [28.3, -11.6]],
  "Dakhla-Oued Ed-Dahab": [[21.5, -17.2], [24.7, -13.1]],
};

const toFeature = (region: string, count: number) => {
  const bounds = REGION_BOUNDS[region];
  if (!bounds) return null;
  const [[south, west], [north, east]] = bounds;
  return {
    type: "Feature",
    properties: { name: region, count },
    geometry: {
      type: "Polygon",
      coordinates: [[
        [west, south],
        [east, south],
        [east, north],
        [west, north],
        [west, south],
      ]],
    },
  };
};

const colorForCount = (count: number, max: number) => {
  if (!count) return "#e5e7eb";
  const ratio = count / Math.max(max, 1);
  if (ratio > 0.75) return "#047857";
  if (ratio > 0.5) return "#0f766e";
  if (ratio > 0.25) return "#38bdf8";
  return "#f59e0b";
};

export default function MapComponent({ projects, regions, sectorFilter = "" }: MapComponentProps) {
  const filteredProjects = sectorFilter
    ? projects.filter((project) => project.secteur === sectorFilter)
    : projects;
  const regionCounts = filteredProjects.reduce<Record<string, number>>((acc, project) => {
    if (project.region) acc[project.region] = (acc[project.region] ?? 0) + 1;
    return acc;
  }, {});
  const maxRegionCount = Math.max(1, ...Object.values(regionCounts));
  const regionGeoJson = {
    type: "FeatureCollection",
    features: regions
      .map((region) => toFeature(region.nom, regionCounts[region.nom] ?? 0))
      .filter(Boolean),
  } as any;

  return (
    <MapContainer
      center={[31.5, -7]}
      zoom={5}
      style={{ height: "520px", width: "100%", borderRadius: "0.75rem" }}
      scrollWheelZoom
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      <GeoJSON
        key={`${sectorFilter}-${filteredProjects.length}`}
        data={regionGeoJson}
        style={(feature) => ({
          color: "#334155",
          weight: 1,
          fillColor: colorForCount(feature?.properties?.count ?? 0, maxRegionCount),
          fillOpacity: 0.22,
        })}
        onEachFeature={(feature, layer) => {
          layer.bindPopup(
            `<strong>${feature.properties.name}</strong><br/>${feature.properties.count} projet(s)`
          );
        }}
      />

      {regions.map((region) => {
        const count = regionCounts[region.nom] ?? 0;
        if (!count) return null;
        return (
          <CircleMarker
            key={`cluster-${region.nom}`}
            center={[region.latitude, region.longitude]}
            radius={Math.min(28, 8 + count * 3)}
            pathOptions={{
              color: "#0f172a",
              weight: 1,
              fillColor: colorForCount(count, maxRegionCount),
              fillOpacity: 0.75,
            }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{region.nom}</p>
                <p>{count} projet(s) dans le filtre courant</p>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}

      {filteredProjects.map((p) => (
        <Marker
          key={p.id}
          position={[p.latitude, p.longitude]}
          icon={sectorIcon(p.secteur ?? "")}
        >
          <Popup minWidth={220}>
            <div className="space-y-1 py-1">
              <p className="font-semibold text-sm leading-snug">{p.titre}</p>
              <p className="text-xs text-gray-500">{p.secteur}</p>
              {p.region && <p className="text-xs text-gray-500">{p.region}</p>}
              {p.stade && (
                <span className="inline-block text-xs bg-gray-100 text-gray-700 rounded px-1.5 py-0.5">
                  {p.stade}
                </span>
              )}
              <p className="text-xs font-semibold text-green-700 pt-1">
                {formatMAD(p.montant_mad)}
              </p>
              {p.score_fiabilite !== null && p.score_fiabilite !== undefined && (
                <p className="text-xs text-gray-400">Score: {p.score_fiabilite}%</p>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
