"use client";
import { useEffect, useRef, useState } from "react";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import { useWorkspace } from "@/lib/workspace";
import type { Project } from "@/lib/types";
function candidates(project: Project, selected: string[]) {
  return {
    type: "FeatureCollection",
    features: project.sites.map((s) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [s.longitude, s.latitude] },
      properties: {
        site_id: s.site_id,
        name: s.name,
        selected: selected.includes(s.site_id),
      },
    })),
  };
}
export default function LocationMap() {
  const w = useWorkspace();
  const project = w.project?.data;
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const latest = useRef(w);
  latest.current = w;
  const [showDestinations, setShowDestinations] = useState(true);
  const [showCatchments, setShowCatchments] = useState(true);
  const [message, setMessage] = useState("Loading local map…");
  useEffect(() => {
    if (!project || !host.current) return;
    let cancelled = false;
    let observer: ResizeObserver | undefined;
    void import("maplibre-gl")
      .then(
        ({
          Map,
          NavigationControl,
          Popup,
          LngLatBounds,
          setWorkerUrl,
          setWorkerCount,
        }) => {
          if (cancelled || !host.current) return;
          try {
            setWorkerUrl("/vendor/maplibre/maplibre-gl-worker.mjs");
            setWorkerCount(1);
            const instance = new Map({
              container: host.current,
              style: {
                version: 8,
                sources: {},
                layers: [
                  {
                    id: "paper",
                    type: "background",
                    paint: { "background-color": "#f7f7f4" },
                  },
                ],
              },
              center: [73.07, 19.055],
              zoom: 11,
              attributionControl: false,
              cooperativeGestures: true,
            });
            map.current = instance;
            instance.addControl(
              new NavigationControl({ showCompass: false }),
              "top-right",
            );
            instance.on("error", () => {
              if (!cancelled)
                setMessage(
                  "A map layer could not load. All candidate inputs remain available in the table.",
                );
            });
            instance.on("load", () => {
              if (cancelled) return;
              instance.addSource("boundary", {
                type: "geojson",
                data: "/demo-boundary.geojson",
              });
              instance.addLayer({
                id: "boundary-fill",
                type: "fill",
                source: "boundary",
                paint: { "fill-color": "#eae8e0", "fill-opacity": 0.7 },
              });
              instance.addLayer({
                id: "boundary-edge",
                type: "line",
                source: "boundary",
                paint: { "line-color": "#c9c7bd", "line-width": 1 },
              });
              instance.addSource("destinations", {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] },
              });
              instance.addLayer({
                id: "destination-pins",
                type: "circle",
                source: "destinations",
                paint: {
                  "circle-radius": 3,
                  "circle-color": "#a9a5b2",
                  "circle-stroke-width": 1,
                  "circle-stroke-color": "white",
                },
              });
              instance.addSource("catchments", {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] },
              });
              instance.addLayer({
                id: "catchment-fill",
                type: "fill",
                source: "catchments",
                paint: { "fill-color": "#7244e5", "fill-opacity": 0.07 },
              });
              instance.addLayer({
                id: "catchment-edge",
                type: "line",
                source: "catchments",
                paint: {
                  "line-color": "#7244e5",
                  "line-width": 1,
                  "line-dasharray": [3, 3],
                },
              });
              instance.addSource("branches", {
                type: "geojson",
                data: {
                  type: "FeatureCollection",
                  features: project.stores.map((s) => ({
                    type: "Feature",
                    geometry: {
                      type: "Point",
                      coordinates: [s.longitude, s.latitude],
                    },
                    properties: { name: s.name },
                  })),
                },
              });
              instance.addLayer({
                id: "branch-pins",
                type: "circle",
                source: "branches",
                paint: {
                  "circle-radius": 6,
                  "circle-color": "#18181b",
                  "circle-stroke-color": "#fff",
                  "circle-stroke-width": 2,
                },
              });
              instance.addSource("candidates", {
                type: "geojson",
                data: candidates(
                  project,
                  latest.current.selection,
                ) as Parameters<GeoJSONSource["setData"]>[0],
              });
              instance.addLayer({
                id: "candidate-pins",
                type: "circle",
                source: "candidates",
                paint: {
                  "circle-radius": ["case", ["get", "selected"], 9, 6],
                  "circle-color": "#7244e5",
                  "circle-stroke-width": ["case", ["get", "selected"], 3, 2],
                  "circle-stroke-color": "#fff",
                },
              });
              const points = [...project.sites, ...project.stores];
              if (points.length) {
                const bounds = new LngLatBounds();
                points.forEach((p) => bounds.extend([p.longitude, p.latitude]));
                instance.fitBounds(bounds, {
                  padding: 50,
                  maxZoom: 12,
                  duration: 0,
                });
              }
              setMessage(
                "SYNTHETIC boundary and location inputs. Purple: candidate sites. Black: fictional branches.",
              );
            });
            instance.on("click", "candidate-pins", (event) => {
              const id = event.features?.[0]?.properties?.site_id;
              const name = event.features?.[0]?.properties?.name;
              if (typeof id === "string") {
                latest.current.toggleSite(id);
                new Popup({ closeButton: true })
                  .setLngLat(event.lngLat)
                  .setText(
                    String(name) +
                      " · use the table to compare up to two sites",
                  )
                  .addTo(instance);
              }
            });
            instance.on("mouseenter", "candidate-pins", () => {
              instance.getCanvas().style.cursor = "pointer";
            });
            instance.on("mouseleave", "candidate-pins", () => {
              instance.getCanvas().style.cursor = "";
            });
            observer = new ResizeObserver(() => instance.resize());
            observer.observe(host.current);
          } catch {
            setMessage(
              "Map rendering is unavailable. Use the candidate table to explore and compare every site.",
            );
          }
        },
      )
      .catch(() =>
        setMessage(
          "Map loading failed. The candidate table remains available.",
        ),
      );
    return () => {
      cancelled = true;
      observer?.disconnect();
      map.current?.remove();
      map.current = null;
    };
  }, [project]);
  useEffect(() => {
    const source = map.current?.getSource("candidates") as
      | GeoJSONSource
      | undefined;
    if (source && project)
      source.setData(
        candidates(project, w.selection) as Parameters<
          GeoJSONSource["setData"]
        >[0],
      );
  }, [w.selection, project]);
  useEffect(() => {
    const instance = map.current;
    if (!instance?.getSource("destinations")) return;
    const geo =
      w.current &&
      w.geoContext?.evaluation_id === w.evaluation?.data.evaluation_id
        ? w.geoContext
        : null;
    const source = instance.getSource("destinations") as GeoJSONSource;
    source.setData({
      type: "FeatureCollection",
      features: (showDestinations ? (geo?.pois ?? []) : []).map((p) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [p.longitude, p.latitude] },
        properties: { category: p.category },
      })),
    });
    const catchment = instance.getSource("catchments") as GeoJSONSource;
    catchment.setData({
      type: "FeatureCollection",
      features: (showCatchments ? (geo?.catchments ?? []) : [])
        .filter((c) => w.selection.includes(c.site_id))
        .map((c) => ({
          type: "Feature",
          geometry: c.geometry,
          properties: { site_id: c.site_id },
        })),
    });
  }, [
    w.geoContext,
    w.current,
    w.evaluation,
    w.selection,
    showDestinations,
    showCatchments,
    message,
  ]);
  return (
    <section className="location-map-section" aria-labelledby="map-heading">
      <div className="section-heading">
        <div>
          <h2 id="map-heading">Location context</h2>
          <p>
            Select purple locations to compare. Grey points are supporting
            destinations; black points are existing branches.
          </p>
        </div>
        <span>{project?.source_status ?? "Source unavailable"}</span>
      </div>
      <div className="map-controls">
        <label className="check-label">
          <input
            type="checkbox"
            checked={showDestinations}
            onChange={(e) => setShowDestinations(e.target.checked)}
          />
          Destinations
        </label>
        <label className="check-label">
          <input
            type="checkbox"
            checked={showCatchments}
            onChange={(e) => setShowCatchments(e.target.checked)}
          />
          Selected catchments
        </label>
      </div>
      <div
        ref={host}
        className="location-map"
        aria-label="Synthetic candidate and branch location map"
      />
      <p role="status" className="helper">
        {message}{" "}
        {w.geoContext && w.current
          ? "Catchments are assumed straight-line radii, not travel-time areas. Road and observed competitor data are unavailable."
          : "Evaluate this scenario to load its supporting geographic evidence."}
      </p>
    </section>
  );
}
