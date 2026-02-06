export default function Loading() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-md bg-muted" />
      <div className="space-y-4">
        <div className="h-6 w-32 animate-pulse rounded bg-muted" />
        <div className="rounded-md border divide-y">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between px-4 py-3">
              <div className="space-y-2">
                <div className="h-4 w-32 animate-pulse rounded bg-muted" />
                <div className="h-3 w-24 animate-pulse rounded bg-muted" />
              </div>
              <div className="h-8 w-16 animate-pulse rounded bg-muted" />
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-4">
        <div className="h-6 w-32 animate-pulse rounded bg-muted" />
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="h-40 animate-pulse rounded-md border bg-muted" />
          <div className="h-40 animate-pulse rounded-md border bg-muted" />
        </div>
      </div>
    </div>
  );
}
