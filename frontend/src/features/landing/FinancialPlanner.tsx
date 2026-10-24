import Link from 'next/link';

export default function FinancialPlanner() {
  return <div className="financial-planner" role="status">
    <h3>Financial analysis awaits a saved evaluation</h3>
    <p>Revenue, incremental network NPV, ROI, payback and portfolio selection must come from the backend. No financial result is calculated by this landing page.</p>
    <Link className="button" href="/app">Open the workspace</Link>
  </div>;
}
