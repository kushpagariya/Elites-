import type { Failure } from "@/lib/workspace";
export function ErrorNotice({
  error,
  retry,
}: {
  error: Failure | null;
  retry?: () => void;
}) {
  if (!error) return null;
  return (
    <div className="message error-message" role="alert">
      <strong>{error.title}</strong>
      <p>{error.message}</p>
      {error.fields.length > 0 && (
        <ul>
          {error.fields.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      )}
      {retry && (
        <button className="secondary" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  );
}
export function Unavailable({ children }: { children: React.ReactNode }) {
  return <p className="unavailable">{children}</p>;
}
