import React, { useCallback, useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export const iso = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10);
export const parse = (d) => new Date(d + 'T00:00:00');
export const fmtDate = (d) => parse(d).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });
export const fmtTime = (t) => { const [h, m] = String(t).split(':'); return `${h % 12 || 12}:${m} ${h < 12 ? 'AM' : 'PM'}`; };
export const or404 = (p) => p.catch((e) => (e.status === 404 ? [] : Promise.reject(e)));
export const when = (d) => {
  const n = Math.round((parse(d) - parse(iso(new Date()))) / 864e5);
  return n === 0 ? 'Today' : n === 1 ? 'Tomorrow' : n > 1 ? `In ${n} days` : 'Past';
};

export function useLoad(fn, deps) {
  const [s, set] = useState({ loading: true });
  const run = useCallback(() => {
    set({ loading: true });
    fn().then((data) => set({ data }), (error) => set({ error }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { run(); }, [run]);
  return { ...s, reload: run };
}

export const Pulse = ({ className }) => (
  <svg className={className} viewBox="0 0 200 40" fill="none" aria-hidden="true">
    <path d="M0 22H50L58 8L68 36L78 2L87 22H120L127 14L133 22H200" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Logo = ({ light }) => (
  <span className={`logo ${light ? 'light' : ''}`}><span className="logo-mark"><Pulse /></span>Clinexa</span>
);

export const Status = ({ s }) => <span className={`pill ${s.toLowerCase()}`}><i />{s[0] + s.slice(1).toLowerCase()}</span>;
export const Loading = () => <div className="skeleton" aria-busy="true"><span /><span /><span /></div>;

export const Note = ({ icon: Icon, title, text, onRetry, children }) => (
  <div className="note">
    {Icon && <div className="note-ico"><Icon size={26} /></div>}
    <h3>{title}</h3>{text && <p>{text}</p>}
    {onRetry && <button className="btn ghost" onClick={onRetry}>Try again</button>}
    {children}
  </div>
);

export const Stat = ({ icon: Icon, tone = 'blue', value, label }) => (
  <div className="stat"><div className={`ico ${tone}`}><Icon size={20} /></div><div><b>{value}</b><span>{label}</span></div></div>
);

export const Head = ({ title, text, children }) => (
  <header className="head"><div><h1>{title}</h1>{text && <p>{text}</p>}</div>{children}</header>
);

export function Calendar({ marked = new Set() }) {
  const [m, setM] = useState(() => { const d = new Date(); return new Date(d.getFullYear(), d.getMonth(), 1); });
  const first = m.getDay();
  const days = new Date(m.getFullYear(), m.getMonth() + 1, 0).getDate();
  const todayIso = iso(new Date());
  const key = (d) => iso(new Date(m.getFullYear(), m.getMonth(), d));
  const cells = [...Array(first).fill(null), ...Array.from({ length: days }, (_, i) => i + 1)];
  const go = (n) => setM(new Date(m.getFullYear(), m.getMonth() + n, 1));
  return (
    <div className="cal">
      <div className="cal-head">
        <b>{m.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}</b>
        <div>
          <button onClick={() => go(-1)} aria-label="Previous month"><ChevronLeft size={16} /></button>
          <button onClick={() => go(1)} aria-label="Next month"><ChevronRight size={16} /></button>
        </div>
      </div>
      <div className="cal-grid">
        {'SMTWTFS'.split('').map((d, i) => <span key={i} className="dow">{d}</span>)}
        {cells.map((d, i) => d
          ? <span key={i} className={`day${key(d) === todayIso ? ' today' : ''}${marked.has(key(d)) ? ' mark' : ''}`}>{d}</span>
          : <span key={i} />)}
      </div>
    </div>
  );
}
