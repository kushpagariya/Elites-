import type { CandidateSite, SiteAnalysis } from "@/lib/types";
import { money } from "@/lib/format";
import { compactMoney } from "@/lib/presentation";

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
  // A shared symmetric display scale preserves the sign and relative magnitude.
  // All values are saved backend cash flows; this computes geometry only.
  const extent = Math.max(1, ...sites.flatMap(site =>
    (analyses.get(site.site_id)?.annual_cashflows_inr ?? []).filter(Number.isFinite).map(Math.abs),
  ));
  return (
    <section aria-labelledby="cashflows-heading">
      <h3 id="cashflows-heading">Annual incremental cash flows</h3>
      <p className="helper">
        Saved network cash flows in INR. Bars share a scale; the centre line is zero.
        Upfront investment is shown separately.
      </p>
      {count === 0 ? (
        <p className="unavailable">
          Annual cash flows have not been supplied for these sites.
        </p>
      ) : (
        <>
        <div className="cashflow-key">{sites.map(site => <span key={site.site_id}><i aria-hidden="true"/>{site.name}</span>)}</div>
        <div className="cashflow-chart" role="group" aria-label="Annual incremental cash flow chart">
          {Array.from({length: count}, (_, index) => <div className="cashflow-year" key={index}>
            <strong>Year {index + 1}</strong>
            {sites.map((site, series) => {
              const value = analyses.get(site.site_id)?.annual_cashflows_inr[index];
              const known = value != null && Number.isFinite(value);
              const width = known ? Math.abs(value) / extent * 50 : 0;
              return <div className="cashflow-row" key={site.site_id} data-series={series}>
                <span>{site.name}</span>
                <div className="cashflow-track" aria-hidden="true"><span className="cashflow-fill" style={{width: `${width}%`, left: `${known && value < 0 ? 50 - width : 50}%`}}/></div>
                <strong title={money(value)} aria-label={money(value)}>{compactMoney(value)}</strong>
              </div>;
            })}
          </div>)}
        </div>
        <details className="cashflow-table"><summary>View exact cash flows</summary>
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
        </details>
        </>
      )}
    </section>
  );
}
