async function getHealth() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/healthz`, {
    cache: "no-store",
  });
  if (!res.ok) return { status: "unknown" };
  return res.json() as Promise<{ status: string }>;
}

export default async function Page() {
  const health = await getHealth();
  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1>Your Morning Brief</h1>
      <p>
        Backend health: <strong>{health.status}</strong>
      </p>
    </main>
  );
}
