export default function BrandMark({ size = 36 }: { size?: number }) {
  return <svg className="brand-mark" aria-hidden="true" viewBox="0 0 40 44" width={size} height={size * 1.1} fill="none">
    <path d="M20 41s15-12.1 15-24A15 15 0 0 0 5 17c0 11.9 15 24 15 24Z" stroke="currentColor" strokeWidth="1.8" />
    <path d="M11.5 18h17M13 18v11h14V18M11.5 18l2-7h13l2 7M17 11l-1 7m7-7 1 7M18 29v-7h5v7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>;
}
