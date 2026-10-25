"use client";
import { useEffect, useRef, useState, useId } from "react";
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl";
import { useWorkspace } from "@/lib/workspace";
import { money, percent } from "@/lib/format";
import { compactMoney } from "@/lib/presentation";
import { hasMapGeometry } from "@/lib/map-data";
import StatusBadge from "@/components/StatusBadge";
import type { Project } from "@/lib/types";

export const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const empty = () => ({ type: "FeatureCollection" as const, features: [] });
function candidateData(
  project: Project,
  selected: string[],
  focused: string | null,
  scores: Map<string, number | null>,
) {
  return {
    type: "FeatureCollection",
    features: project.sites.map((s) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [s.longitude, s.latitude] },
      properties: {
        site_id: s.site_id,
        name: s.name,
        selected: selected.includes(s.site_id),
        focused: s.site_id === focused,
        score: scores.get(s.site_id) ?? null,
      },
    })),
  };
}
export default function LocationMap({
  selectedSiteIds,
  compact = false,
}: {
  selectedSiteIds?: string[];
  compact?: boolean;
}) {
  const w = useWorkspace();
  const project = w.project?.data;
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<LibreMap | null>(null);
  const latest = useRef(w);
  latest.current = w;
  const [ready, setReady] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pois, setPois] = useState(true);
  const [competitors, setCompetitors] = useState(true);
  const [catchments, setCatchments] = useState(true);
  const [opportunity, setOpportunity] = useState(false);
  const [infrastructure, setInfrastructure] = useState(true);
  const titleId = useId();
  const selected = selectedSiteIds ?? w.selection;
  const geo =
    w.geoContext && w.evaluation && !w.dirty &&
    w.geoContext?.evaluation_id === w.evaluation?.data.evaluation_id
      ? w.geoContext
      : w.referenceGeo;
  const focused = project?.sites.find((s) => s.site_id === w.focusedSiteId);
  const analysis = !w.dirty && w.evaluation?.data.scenario_id === w.scenario?.scenario_id
    ? w.evaluation?.data.site_analyses.find(
        (s) => s.site_id === focused?.site_id,
      )
    : undefined;
  const view = () => {
    const instance = map.current;
    if (!instance || !project) return;
    const points = [...project.sites, ...project.stores];
    if (!points.length) return;
    const lng = points.map((p) => p.longitude),
      lat = points.map((p) => p.latitude);
    instance.fitBounds(
      [
        [Math.min(...lng), Math.min(...lat)],
        [Math.max(...lng), Math.max(...lat)],
      ],
      { padding: compact ? 45 : 65, maxZoom: 13, duration: 0 },
    );
  };
  const fitSelected = () => {
    const instance = map.current;
    const sites =
      project?.sites.filter((s) => selected.includes(s.site_id)) ?? [];
    if (!instance || !sites.length) return view();
    const lng = sites.map((p) => p.longitude),
      lat = sites.map((p) => p.latitude);
    instance.fitBounds(
      [
        [Math.min(...lng), Math.min(...lat)],
        [Math.max(...lng), Math.max(...lat)],
      ],
      { padding: 75, maxZoom: 14, duration: 0 },
    );
  };
  useEffect(() => {
    if (!project || !host.current) return;
    let cancelled = false;
    let observer: ResizeObserver | undefined;
    setLoading(true);
    setError(null);
    setReady(false);
    const timer = setTimeout(() => {
      if (!cancelled) {
        setLoading(false);
        setError(
          "The city map is taking too long to load. Check your connection and retry.",
        );
      }
    }, 18000);
    void import("maplibre-gl")
      .then(
        ({
          Map,
          NavigationControl,
          AttributionControl,
          Popup,
          Marker,
          setWorkerUrl,
          setWorkerCount,
        }) => {
          if (cancelled || !host.current) return;
          try {
            setWorkerUrl("/vendor/maplibre/maplibre-gl-worker.mjs");
            setWorkerCount(1);
            const points = [...project.sites, ...project.stores];
            const centre: [number, number] = points.length
              ? [
                  points.reduce((s, p) => s + p.longitude, 0) / points.length,
                  points.reduce((s, p) => s + p.latitude, 0) / points.length,
                ]
              : [77.63, 12.91];
            const instance = new Map({
              container: host.current,
              style: BASEMAP_STYLE,
              center: centre,
              zoom: 11,
              attributionControl: false,
              cooperativeGestures: true,
              pitchWithRotate: false,
              dragRotate: false,
            });
            map.current = instance;
            instance.addControl(
              new NavigationControl({ showCompass: false }),
              "top-right",
            );
            instance.addControl(
              new AttributionControl({
                compact: true,
              }),
              "bottom-right",
            );
            instance.on("error", (event) => {
              console.warn('StoreScout map resource failed', event.error?.message);
              if (!cancelled) {
                clearTimeout(timer);
                setLoading(false);
                setError(
                  "Some map tiles could not load. Retry the map; location cards remain available.",
                );
              }
            });
            instance.on("load", () => {
              if (cancelled) return;
              clearTimeout(timer);
              setLoading(false);
              setError(null);
            });
            // Install data layers as soon as the style is ready. Tile/font
            // delays must not prevent the location sources from attaching.
            instance.on("style.load", () => {
              if (cancelled) return;
              instance.addSource("catchments", {
                type: "geojson",
                data: empty(),
              });
              instance.addLayer({
                id: "catchment-fill",
                type: "fill",
                source: "catchments",
                paint: { "fill-color": "#a83d24", "fill-opacity": 0.09 },
              });
              instance.addLayer({
                id: "catchment-edge",
                type: "line",
                source: "catchments",
                paint: {
                  "line-color": "#a83d24",
                  "line-width": 1.2,
                  "line-dasharray": [3, 2],
                },
              });
              instance.addSource("destinations", {
                type: "geojson",
                data: empty(),
              });
              instance.addSource('competitors', {type: 'geojson', data: empty(), cluster: true, clusterMaxZoom: 13, clusterRadius: 42});
              instance.addLayer({id:'competitor-clusters',type:'circle',source:'competitors',filter:['has','point_count'],paint:{'circle-color':'#77503b','circle-radius':18,'circle-stroke-color':'#fff','circle-stroke-width':2}});
              instance.addLayer({id:'competitor-counts',type:'symbol',source:'competitors',filter:['has','point_count'],layout:{'text-field':['get','point_count_abbreviated'],'text-size':12},paint:{'text-color':'#fff'}});
              instance.addLayer({id:'competitor-pins',type:'circle',source:'competitors',filter:['!', ['has','point_count']],paint:{'circle-radius':5,'circle-color':'#d29b38','circle-stroke-color':'#77503b','circle-stroke-width':2}});
              instance.addLayer({
                id: "destination-pins",
                type: "circle",
                source: "destinations",
                paint: {
                  "circle-radius": 4,
                  "circle-color": [
                    "case",
                    ["==", ["get", "category"], "competitor"],
                    "#77503b",
                    ["get", "relevant"],
                    "#297f79",
                    "#9ca996",
                  ],
                  "circle-stroke-color": "white",
                  "circle-stroke-width": 1,
                  "circle-opacity": 0.85,
                },
              });
              instance.addSource("infrastructure", {
                type: "geojson",
                data: empty(),
              });
              instance.addLayer({
                id: "infra-lines",
                type: "line",
                source: "infrastructure",
                filter: ["!=", ["geometry-type"], "Point"],
                paint: {
                  "line-color": "#996020",
                  "line-width": 3,
                  "line-dasharray": [3, 2],
                },
              });
              instance.addLayer({
                id: "infra-pins",
                type: "circle",
                source: "infrastructure",
                filter: ["==", ["geometry-type"], "Point"],
                paint: {
                  "circle-radius": 8,
                  "circle-color": "#fff",
                  "circle-stroke-color": "#996020",
                  "circle-stroke-width": 3,
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
                  "circle-radius": 8,
                  "circle-color": "#203c32",
                  "circle-stroke-color": "white",
                  "circle-stroke-width": 2,
                },
              });
              instance.addSource("candidates", {
                type: "geojson",
                data: empty(),
              });
              instance.addLayer({
                id: "opportunity-halos",
                filter: [">=", ["coalesce", ["get", "score"], -1], 0],
                type: "circle",
                source: "candidates",
                paint: {
                  "circle-radius": [
                    "interpolate",
                    ["linear"],
                    ["coalesce", ["get", "score"], 0],
                    0,
                    12,
                    100,
                    34,
                  ],
                  "circle-color": "#a83d24",
                  "circle-opacity": 0,
                },
              });
              instance.addLayer({
                id: "candidate-pins",
                type: "circle",
                source: "candidates",
                paint: {
                  "circle-radius": [
                    "case",
                    ["get", "focused"],
                    10,
                    ["get", "selected"],
                    8,
                    6,
                  ],
                  "circle-color": compact
                    ? ["case", ["get", "selected"], "#a83d24", "#9ca996"]
                    : "#a83d24",
                  "circle-stroke-width": ["case", ["get", "selected"], 3, 2],
                  "circle-stroke-color": "white",
                },
              });
              instance.on("click", "candidate-pins", (event) => {
                const id = event.features?.[0]?.properties?.site_id;
                if (typeof id !== "string") return;
                latest.current.focusSite(id);
              });
              instance.on('click', 'competitor-clusters', async event => {
                const feature = event.features?.[0];
                if (!feature || feature.geometry.type !== 'Point') return;
                const zoom = await (instance.getSource('competitors') as GeoJSONSource).getClusterExpansionZoom(Number(feature.properties.cluster_id));
                instance.easeTo({center: feature.geometry.coordinates as [number,number], zoom});
              });
              instance.on('click', 'competitor-pins', event => {
                latest.current.focusSite(null);
                const p = event.features?.[0]?.properties;
                if (p) new Popup().setLngLat(event.lngLat).setText(`${p.name || 'Unnamed mapped shop'} · ${p.category} · ${p.source_status} · source: ${p.source_id}. Contextual competitor evidence. Sales and NPV are unavailable: no store financial observations were collected.`).addTo(instance);
              });
              instance.on('click','branch-pins',event => {
                latest.current.focusSite(null);
                new Popup().setLngLat(event.lngLat).setText(`${event.features?.[0]?.properties?.name} · Fictional existing branch (SYNTHETIC). Used for modelled displacement; no observed branch sales.`).addTo(instance);
              });
              project.sites.forEach((site, index) => {
                const button = document.createElement('button');
                button.type='button'; button.className='candidate-map-pin';
                button.textContent=String(index+1); button.dataset.siteId=site.site_id;
                button.setAttribute('aria-label','Candidate location '+site.name);
                button.addEventListener('click',event=>{event.stopPropagation();latest.current.focusSite(site.site_id);});
                new Marker({element:button}).setLngLat([site.longitude,site.latitude]).addTo(instance);
              });
              instance.on("mouseenter", "candidate-pins", () => {
                instance.getCanvas().style.cursor = "pointer";
              });
              instance.on("mouseleave", "candidate-pins", () => {
                instance.getCanvas().style.cursor = "";
              });
              const describeEvent = (
                event: import("maplibre-gl").MapLayerMouseEvent,
              ) => {
                const p = event.features?.[0]?.properties;
                if (p)
                  new Popup()
                    .setLngLat(event.lngLat)
                    .setText(
                      String(p.name) +
                        " · " +
                        String(p.status) +
                        " · " +
                        (p.hypothetical
                          ? "Hypothetical"
                          : "Source-labelled evidence") +
                        " · source opening " +
                        String(p.opening_date ?? "unknown"),
                    )
                    .addTo(instance);
              };
              instance.on("click", "infra-pins", describeEvent);
              instance.on("click", "infra-lines", describeEvent);
              instance.on("click", "destination-pins", (event) => {
                const p = event.features?.[0]?.properties;
                if (p)
                  new Popup()
                    .setLngLat(event.lngLat)
                    .setText(
                      String(p.category) +
                        " · " +
                        String(p.source_status) +
                        " destination · POI proxy, not footfall",
                    )
                    .addTo(instance);
              });
              setReady(true);
              view();
            });
            observer = new ResizeObserver(() => instance.resize());
            observer.observe(host.current);
          } catch {
            clearTimeout(timer);
            setLoading(false);
            setError(
              "This browser could not display the city map. Use the location cards or retry in a browser with WebGL enabled.",
            );
          }
        },
      )
      .catch(() => {
        clearTimeout(timer);
        setLoading(false);
        setError("The map could not start. Location cards remain available.");
      });
    return () => {
      cancelled = true;
      clearTimeout(timer);
      observer?.disconnect();
      map.current?.remove();
      map.current = null;
    };
    // Project coordinates are stable; selection is synchronized through sources below.
  }, [project, attempt, compact]);
  useEffect(() => {
    const instance = map.current;
    if (!ready || !instance || !project) return;
    const profiles = w.current ? (w.evaluation?.data.site_analyses ?? []) : [];
    const scores = new Map(
      profiles.map((s) => [
        s.site_id,
        s.dayparts?.find((p) => p.time_bin === w.activePeriod)
          ?.opportunity_index ?? null,
      ]),
    );
    (instance.getSource("candidates") as GeoJSONSource).setData(
      candidateData(project, selected, w.focusedSiteId, scores) as Parameters<
        GeoJSONSource["setData"]
      >[0],
    );
    host.current?.querySelectorAll<HTMLButtonElement>('.candidate-map-pin').forEach(button => {
      button.setAttribute('aria-pressed',String(selected.includes(button.dataset.siteId ?? '')));
      button.dataset.focused=String(button.dataset.siteId === w.focusedSiteId);
    });
    const categories = new Set(
      profiles
        .filter((s) => s.site_id === (w.focusedSiteId ?? selected[0]))
        .flatMap(
          (s) =>
            s.dayparts
              ?.find((p) => p.time_bin === w.activePeriod)
              ?.categories.filter((c) => c.weighted_opportunity > 0)
              .map((c) => c.category) ?? [],
        ),
    );
    (instance.getSource("destinations") as GeoJSONSource).setData({
      type: "FeatureCollection",
      features: (geo?.pois ?? []).filter(p => p.category !== "competitor" && pois).map((p) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [p.longitude, p.latitude] },
        properties: {
          category: p.category,
          source_status: p.source_status,
          relevant: categories.has(p.category),
        },
      })),
    });
    (instance.getSource('competitors') as GeoJSONSource).setData({type:'FeatureCollection',features:(geo?.pois ?? []).filter(p => p.category === 'competitor').map(p => ({type:'Feature',geometry:{type:'Point',coordinates:[p.longitude,p.latitude]},properties:{name:p.name,category:p.category,source_id:p.source_id,source_status:p.source_status}}))});
    for (const layer of ['competitor-clusters','competitor-counts','competitor-pins']) instance.setLayoutProperty(layer,'visibility',competitors ? 'visible' : 'none');
    (instance.getSource("catchments") as GeoJSONSource).setData({
      type: "FeatureCollection",
      features: (catchments ? (geo?.catchments ?? []) : [])
        .filter(
          (c) => selected.includes(c.site_id) || c.site_id === w.focusedSiteId,
        )
        .map((c) => ({
          type: "Feature",
          geometry: c.geometry,
          properties: { site_id: c.site_id },
        })),
    });
    const events = infrastructure
      ? w.infrastructure.filter(hasMapGeometry)
      : [];
    (instance.getSource("infrastructure") as GeoJSONSource).setData({
      type: "FeatureCollection",
      features: events.map((e) => ({
        type: "Feature",
        geometry: e.geometry!,
        properties: {
          name: e.name,
          status: e.status,
          opening_date: e.expected_open_date ?? e.assumed_demo_open_date,
          hypothetical: e.hypothetical_demo,
        },
      })),
    } as Parameters<GeoJSONSource["setData"]>[0]);
    instance.setPaintProperty(
      "infra-pins",
      "circle-color",
      w.scenario?.assumptions.infrastructure_state === "current"
        ? "#fff"
        : "#ddc094",
    );
    instance.setPaintProperty(
      "opportunity-halos",
      "circle-opacity",
      opportunity && w.current ? 0.16 : 0,
    );
  }, [
    ready,
    project,
    selected,
    w.focusedSiteId,
    w.activePeriod,
    w.current,
    w.evaluation,
    geo,
    pois,
    competitors,
    catchments,
    opportunity,
    infrastructure,
    w.infrastructure,
    w.scenario?.scenario_id,
  ]);
  return (
    <section
      className={"city-map-panel" + (compact ? " compact" : "")}
      aria-labelledby={titleId}
    >
      <div className="map-titlebar">
        <h2 id={titleId}>Explore {project?.city ?? "your city"}</h2>
        <div className="map-view-actions">
          <button
            type="button"
            className="secondary"
            onClick={fitSelected}
            disabled={!ready}
          >
            Fit selection
          </button>
          <button
            type="button"
            className="secondary"
            onClick={view}
            disabled={!ready}
          >
            Reset view
          </button>
        </div>
      </div>
      <div className={'city-map-stage' + (error && !ready ? ' map-unavailable' : '')}>
        <div
          ref={host}
          className="location-map"
          aria-label="City streets with candidate locations and existing stores"
        />
        {loading && (
          <div className="map-loading" role="status">
            <span className="loading-dot" />
            Loading city streets…
          </div>
        )}
        {error && (
          <div className="map-error" role="status">
            <strong>Map connection interrupted</strong>
            <p>{error}</p>
            <button
              className="secondary"
              onClick={() => setAttempt((n) => n + 1)}
            >
              Retry map
            </button>
          </div>
        )}
        {focused && ready && (
          <div className="map-site-card">
            <div className="section-heading">
              <strong>{focused.name}</strong>
              <button
                type="button"
                className="icon-close secondary"
                aria-label="Close location details"
                onClick={() => w.focusSite(null)}
              >
                ×
              </button>
            </div>
            <p className="helper">Candidate location · {w.scenario?.name}</p>
            {analysis ? <><StatusBadge status={analysis.failfast.status} />
            <dl>
              <div>
                <dt>Year 1 sales</dt>
                <dd title={money(analysis?.annual_revenue_inr)}>{compactMoney(analysis?.annual_revenue_inr)}</dd>
              </div>
              <div>
                <dt>Incremental NPV</dt>
                <dd title={money(analysis?.npv_inr)}>{compactMoney(analysis?.npv_inr)}</dd>
              </div>
            </dl></> : <><p>No saved analysis for these settings. Run analysis to see annual sales, incremental NPV and risk status.</p><button disabled={w.busy || w.dirty} onClick={() => void w.evaluate()}>Run Analysis</button>{w.dirty && <p className="helper">Save or reset your edits first.</p>}</>}
            {!compact && (
              <button
                className="secondary"
                disabled={
                  !selected.includes(focused.site_id) && selected.length === 2
                }
                onClick={() => w.toggleSite(focused.site_id)}
              >
                {selected.includes(focused.site_id)
                  ? "Remove from comparison"
                  : "Add to comparison"}
              </button>
            )}
          </div>
        )}
      </div>
      <div className="map-legend">
        <span>
          <i className="legend-dot purple" />
          {compact ? "Recommended locations" : `${project?.sites.length ?? 0} candidate locations`}
        </span>
        {compact && (
          <span>
            <i className="legend-dot other" />
            Other candidates
          </span>
        )}
        <span>
          <i className="legend-dot ink" />
          {project?.stores.length ?? 0} fictional existing branches
        </span>
        {geo && pois && (
          <span>
            <i className="legend-dot teal" />
            POI categories
          </span>
        )}
        <span><i className="legend-dot" style={{background: "#d29b38"}}/>{geo ? `${geo.pois.filter(p => p.category === 'competitor').length} mapped competitors ${competitors ? '' : '(hidden)'}` : w.referenceGeoError ? 'Competitor data unavailable' : 'Loading competitor data…'}</span>
        {infrastructure && w.infrastructure.some(hasMapGeometry) && (
          <span>
            <i className="legend-dot amber" />
            Infrastructure · assumed opening
          </span>
        )}
        <span className="map-data-label">
          Location inputs: {project?.source_status ?? "unknown"}
        </span>
      </div>
      {w.referenceGeoError && !geo && <p className="helper map-data-warning" role="status">Neighbourhood layers are unavailable. <button className="secondary" onClick={() => void w.retryGeography()}>Retry neighbourhood data</button></p>}
      <details className="map-layers">
        <summary>Map layers &amp; data</summary>
        <div className="layer-options">
          {[
            ["Destinations", pois, setPois, !geo],
            ["Mapped competitor POIs", competitors, setCompetitors, !geo],
            ["Location catchments", catchments, setCatchments, !geo],
            ["DaypartDNA opportunity", opportunity, setOpportunity, !w.current],
            [
              "Infrastructure",
              infrastructure,
              setInfrastructure,
              !w.infrastructure.some(hasMapGeometry),
            ],
          ].map(([name, value, setter, disabled]) => (
            <label className="check-label" key={String(name)}>
              <input
                type="checkbox"
                checked={Boolean(value)}
                disabled={Boolean(disabled)}
                onChange={(e) =>
                  (setter as (value: boolean) => void)(e.target.checked)
                }
              />
              {String(name)}
            </label>
          ))}
        </div>
        <p className="helper">Competitor shops are contextual mapped evidence, available before analysis. Clusters expand as you zoom in. Only the {project?.sites.length ?? 0} candidates can enter comparison or portfolio; adding contextual map records does not raise this limit.</p>
        <p className="helper">
          {geo
            ? "Catchments show assumed straight-line radii. DaypartDNA circles show within-location opportunity, not measured footfall or a cross-city score."
            : "Mapped evidence is unavailable. Retry neighbourhood data; financial analysis is a separate step."}{" "}
          Streets come from the basemap; its labels are not analytical evidence.
          Proposed infrastructure is not treated as operating today. No offline
          map cache is bundled.
        </p>
        <p className="helper">
          Saved infrastructure state:{" "}
          {w.scenario?.assumptions.infrastructure_state ?? "Today"}.{" "}
          {analysis?.infrastructure_exposure
            ?.map((e) =>
              e.hypothetical
                ? "Hypothetical effect " + percent(e.assumed_effect_fraction)
                : "",
            )
            .join(" ")}
        </p>
      </details>
    </section>
  );
}
