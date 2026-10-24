import Link from "next/link";
import type { CandidateSite, SiteAnalysis } from "@/lib/types";
import { money, percent, years } from "@/lib/format";
import { compactMoney } from "@/lib/presentation";
import StatusBadge from "@/components/StatusBadge";
export default function InvestmentCard({
  site,
  analysis,
}: {
  site: CandidateSite;
  analysis?: SiteAnalysis;
}) {
  return (
    <article className="investment-card">
      <div className="section-heading">
        <h3>{site.name}</h3>
        <StatusBadge status={analysis?.failfast.status} />
      </div>
      <dl className="investment-primary">
        <div>
          <dt title="Net present value: future network cash flows less initial investment, discounted to today.">
            Network NPV
          </dt>
          <dd title={money(analysis?.npv_inr)}>
            {compactMoney(analysis?.npv_inr)}
          </dd>
        </div>
        <div>
          <dt>Year 1 sales</dt>
          <dd title={money(analysis?.annual_revenue_inr)}>
            {compactMoney(analysis?.annual_revenue_inr)}
          </dd>
        </div>
        <div>
          <dt>Operating profit</dt>
          <dd title={money(analysis?.operating_profit_inr)}>
            {compactMoney(analysis?.operating_profit_inr)}
          </dd>
        </div>
      </dl>
      <dl className="comparison-metrics">
        <div>
          <dt>Investment</dt>
          <dd>{money(site.capex_inr)}</dd>
        </div>
        <div>
          <dt>ROI</dt>
          <dd>{percent(analysis?.roi_fraction)}</dd>
        </div>
        <div>
          <dt>Payback</dt>
          <dd>{years(analysis?.payback_years)}</dd>
        </div>
        <div>
          <dt>Existing-store contribution lost · year 1</dt>
          <dd>{money(analysis?.lost_existing_contribution_inr)}</dd>
        </div>
      </dl>
      {analysis ? (
        <>
          <div className="sensitivity-strip">
            {["low", "base", "high"].map((key) => (
              <div key={key}>
                <span>{key} NPV</span>
                <strong title={money(analysis.sensitivity?.[key]?.npv_inr)}>
                  {compactMoney(analysis.sensitivity?.[key]?.npv_inr)}
                </strong>
              </div>
            ))}
          </div>
          <p className="risk-reason">
            {analysis.failfast.reasons[0] ??
              "No rules failed in the evaluated cases."}
          </p>
          {analysis.failfast.status !== "VIABLE" && (
            <Link className="text-link" href="/app/scenarios">
              What could improve this? →
            </Link>
          )}
          <details>
            <summary>Why this result?</summary>
            <ul>
              {analysis.drivers.slice(0, 3).map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
            {analysis.failfast.reasons.length > 0 && (
              <>
                <h4>All risk reasons</h4>
                <ul>
                  {analysis.failfast.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </>
            )}
            <p>
              Monthly rent: {money(analysis.effective_inputs?.monthly_rent_inr)}
              . Gross margin:{" "}
              {percent(analysis.effective_inputs?.gross_margin_fraction)}.
            </p>
            <h4>Existing-store impact</h4>
            <ul>
              {analysis.branch_impacts?.map((b) => (
                <li key={b.store_id}>
                  {b.store_id}: {money(b.lost_contribution_inr)} contribution
                  lost in year one.
                </li>
              ))}
            </ul>
            <p className="helper">
              Low case: −20% spending and +10% rent. High: +20% spending,
              unchanged rent. These are assumptions, not prediction intervals.
              Operating profit is before existing-store losses; NPV and ROI
              include them.
            </p>
            <p className="helper">
              Sources: {analysis.source_ids.join(", ")}. Monetary values are
              INR. Unrecovered payback is not zero.
            </p>
          </details>
        </>
      ) : (
        <p className="helper">
          Run the saved scenario to see this location’s investment case.
        </p>
      )}
    </article>
  );
}
