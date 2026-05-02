export default function Topbar({ title, health, onMenuToggle }) {
  const checks = health?.checks || {}

  const pills = [
    { label: 'API', status: checks.api?.status },
    { label: 'Database', status: checks.database?.status },
    { label: 'Simulator', status: checks.simulator?.status },
  ]

  return (
    <div className="topbar">
      <div className="topbar-left">
        <button className="btn-ghost" onClick={onMenuToggle} style={{ display: 'none', fontSize: '1.2rem' }} id="menu-toggle">☰</button>
        <h2 className="topbar-title">{title}</h2>
      </div>
      <div className="topbar-right">
        {pills.map(p => {
          const ok = ['up', 'connected', 'running', 'ready', 'healthy'].includes(p.status)
          return (
            <div key={p.label} className="health-pill">
              <span className={`health-dot ${ok ? 'ok' : p.status ? 'warn' : 'bad'}`} />
              {p.label}
            </div>
          )
        })}
      </div>
    </div>
  )
}
