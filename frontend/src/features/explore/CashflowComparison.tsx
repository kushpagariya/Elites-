import type { CandidateSite, SiteAnalysis } from "@/lib/types";
import { money } from "@/lib/format";

export default function CashflowComparison({
  sites,
  analyses,
}: {
  sites: CandidateSite[];
  analyses: Map<string, SiteAnalysis>;
}) {
  const count = Math.max(
    0,
    ...sites.map(
      (site) => analyses.get(site.site_id)?.annual_cashflows_inr.length ?? 0,
    ),
  );
  return (
    <section aria-labelledby="cashflows-heading">
      <h3 id="cashflows-heading">Annual incremental cash flows</h3>
      <p className="helper">
        Saved network cash flows in INR. CAPEX is shown separately; no cash
        flows are inferred in the browser.
      </p>
      {count === 0 ? (
        <p className="unavailable">
          Annual cash flows have not been supplied for these sites.
        </p>
      ) : (
        <div
          className="table-scroll"
          role="region"
          aria-label="Annual incremental cash flow comparison"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th scope="col">Projection year</th>
                {sites.map((site) => (
                  <th key={site.site_id} scope="col" className="numeric">
                    {site.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: count }, (_, index) => (
                <tr key={index}>
                  <th scope="row">Year {index + 1}</th>
                  {sites.map((site) => (
                    <td key={site.site_id} className="numeric">
                      {money(
                        analyses.get(site.site_id)?.annual_cashflows_inr[index],
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
