import type { InfrastructureEvent } from "./types";
export function isPosition(value: unknown): value is [number, number] {
  return (
    Array.isArray(value) &&
    value.length >= 2 &&
    typeof value[0] === "number" &&
    typeof value[1] === "number" &&
    Number.isFinite(value[0]) &&
    Number.isFinite(value[1]) &&
    Math.abs(value[0]) <= 180 &&
    Math.abs(value[1]) <= 90
  );
}
export function hasMapGeometry(event: InfrastructureEvent): boolean {
  const g = event.geometry;
  if (!g) return false;
  if (g.type === "Point") return isPosition(g.coordinates);
  if (g.type === "LineString")
    return (
      Array.isArray(g.coordinates) &&
      g.coordinates.length >= 2 &&
      g.coordinates.every(isPosition)
    );
  if (g.type === "Polygon") {
    const rings: unknown = g.coordinates;
    return (
      Array.isArray(rings) &&
      rings.length > 0 &&
      rings.every((ring: unknown) => {
        if (!Array.isArray(ring) || ring.length < 4 || !ring.every(isPosition))
          return false;
        const first = ring[0] as [number, number],
          last = ring[ring.length - 1] as [number, number];
        return first[0] === last[0] && first[1] === last[1];
      })
    );
  }
  return false;
}
