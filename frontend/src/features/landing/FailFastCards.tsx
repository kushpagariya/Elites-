import Link from 'next/link';

export default function FailFastCards() {
  return <div className="failfast-container">
    <h3>Know what must change before committing</h3>
    <p>FailFast will explain failed rules and return a verified rent or sales threshold from a saved evaluation. Rescue analysis is currently unavailable.</p>
    <Link className="button" href="/app">Check workspace availability</Link>
  </div>;
}
