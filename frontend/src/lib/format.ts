export const money = (value: number | null | undefined) =>
  value == null
    ? "Unavailable"
    : new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }).format(value);
export const percent = (value: number | null | undefined) =>
  value == null
    ? "Unavailable"
    : new Intl.NumberFormat("en-IN", {
        style: "percent",
        maximumFractionDigits: 1,
      }).format(value);
export const years = (value: number | null | undefined) =>
  value == null
    ? "Not recovered / not available"
    : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(
        value,
      ) + " years";
