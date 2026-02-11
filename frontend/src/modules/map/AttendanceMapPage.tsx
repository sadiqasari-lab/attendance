import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import type { MapAttendanceEvent } from "@/types";

export function AttendanceMapPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [events, setEvents] = useState<MapAttendanceEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!tenantSlug) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/${tenantSlug}/attendance/map/`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const data: MapAttendanceEvent = JSON.parse(event.data);
        setEvents((prev) => {
          // Update or add event by employee_id
          const idx = prev.findIndex((e) => e.employee_id === data.employee_id);
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = data;
            return updated;
          }
          return [...prev, data];
        });
      } catch {
        // Ignore malformed messages
      }
    };

    return () => {
      ws.close();
    };
  }, [tenantSlug]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("map.title")}
        </h2>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              connected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {connected ? "Connected" : "Disconnected"}
          </span>
          <span className="text-sm text-gray-400 dark:text-gray-500">
            &middot; {t("map.employees_online")}: {events.length}
          </span>
        </div>
      </div>

      {/* Map container — uses Leaflet */}
      <div className="card overflow-hidden p-0">
        <div
          id="attendance-map"
          className="h-[calc(100vh-220px)] min-h-[400px] bg-gray-100 dark:bg-gray-900 relative"
        >
          {/* Map will be rendered here if leaflet is loaded; fallback: event list */}
          <MapContent events={events} />
        </div>
      </div>

      {/* Event list below map */}
      {events.length > 0 && (
        <div className="card">
          <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
            {t("dashboard.recent_activity")}
          </h3>
          <div className="max-h-60 overflow-y-auto space-y-2">
            {events.map((ev) => (
              <div
                key={ev.employee_id}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm dark:bg-gray-700"
              >
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {ev.employee_name}
                  </span>
                  <span className="ms-2 text-xs text-gray-500 dark:text-gray-400">
                    {ev.event === "clock_in" ? "Clocked In" : "Clocked Out"}
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Map content component — renders Leaflet map with employee markers.
 * Falls back to a placeholder if Leaflet isn't available at runtime.
 */
function MapContent({ events }: { events: MapAttendanceEvent[] }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());

  useEffect(() => {
    let L: typeof import("leaflet") | undefined;
    try {
      L = require("leaflet");
    } catch {
      return; // Leaflet not available
    }

    if (!mapRef.current || leafletMapRef.current) return;

    // Default to Riyadh center
    const map = L.map(mapRef.current).setView([24.7136, 46.6753], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    leafletMapRef.current = map;

    return () => {
      map.remove();
      leafletMapRef.current = null;
    };
  }, []);

  useEffect(() => {
    let L: typeof import("leaflet") | undefined;
    try {
      L = require("leaflet");
    } catch {
      return;
    }

    const map = leafletMapRef.current;
    if (!map) return;

    events.forEach((ev) => {
      const lat = parseFloat(ev.latitude);
      const lng = parseFloat(ev.longitude);
      if (isNaN(lat) || isNaN(lng)) return;

      const existing = markersRef.current.get(ev.employee_id);
      if (existing) {
        existing.setLatLng([lat, lng]);
        existing.setPopupContent(
          `<b>${ev.employee_name}</b><br>${ev.event} at ${
            ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ""
          }`
        );
      } else {
        const marker = L!
          .marker([lat, lng])
          .addTo(map)
          .bindPopup(
            `<b>${ev.employee_name}</b><br>${ev.event} at ${
              ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ""
            }`
          );
        markersRef.current.set(ev.employee_id, marker);
      }
    });
  }, [events]);

  return <div ref={mapRef} className="h-full w-full" />;
}

// Type declaration for dynamic import
declare const L: typeof import("leaflet");
