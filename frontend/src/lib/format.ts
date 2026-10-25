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

export function methodLabel(
  mode:
    | "model_simulated"
    | "model_real_evaluated"
    | "scenario_assumptions"
    | undefined,
) {
  switch (mode) {
    case "model_simulated":
      return "Trained model — synthetic data; real-world accuracy not established.";
    case "model_real_evaluated":
      return "Model evaluated on real data";
    case "scenario_assumptions":
      return "Assumption-based estimate; trained model unavailable.";
    default:
      return "Estimation mode unavailable until a saved evaluation completes.";
  }
}
