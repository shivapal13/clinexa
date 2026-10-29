import React, { useCallback, useEffect, useState } from 'react';
import { Routes, Route, NavLink, Navigate, Outlet, Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Stethoscope, CalendarDays, FileText, User, LogOut, Search, ShieldCheck, Sparkles } from 'lucide-react';
import { api, tokenStore } from './api';
import { Ctx, useApp } from './ctx';
import { Loading, Logo } from './ui';
import { Landing, Auth } from './public';
import { Overview, Doctors, Appointments, DoctorHome, Records, Profile, AddDoctorProfile } from './pages';

function Shell() {
  const { user, profile, isAdmin, signOut } = useApp();
  const nav = useNavigate();
  const doctor = user.role === 'Doctor';
  const items = doctor
    ? [['/', 'Appointments', CalendarDays, true], ['/profile', 'Profile', User]]
    : [['/', 'Overview', LayoutDashboard, true], ['/doctors', 'Doctors', Stethoscope], ['/appointments', 'Visits', CalendarDays], ['/records', 'Records', FileText], ['/profile', 'Profile', User]];
  if (isAdmin) items.push(['/admin/doctors', 'Doctor setup', ShieldCheck]);
  return (
    <div className="app">
      <aside className="side">
        <Logo />
        <div className="nav-label">Workspace</div>
        <nav className="nav" aria-label="Main">
          {items.map(([to, label, Icon, end]) => <NavLink key={to} to={to} end={end}><Icon size={20} />{label}</NavLink>)}
        </nav>
        <div className="side-note">
          <div className="side-note-icon"><ShieldCheck size={18} /></div>
          <b>Your care, together</b>
          <p>Appointments, notes and prescriptions in one secure place.</p>
        </div>
        <div className="me">
          <div className="avatar">{user.name[0]?.toUpperCase()}</div>
          <div><b>{user.name}</b><small>{user.role}</small></div>
          <button className="icon-btn" onClick={signOut} aria-label="Sign out"><LogOut size={18} /></button>
        </div>
      </aside>
      <div className="content">
        <div className="topbar">
          <div className="topbar-copy"><span><Sparkles size={15} /> A healthier day starts here</span></div>
          <div className="topbar-actions">
            {!doctor && (
              <form className="tsearch" onSubmit={(e) => { e.preventDefault(); const q = new FormData(e.target).get('q').trim(); if (q) nav(`/doctors?q=${encodeURIComponent(q)}`); }}>
                <Search size={18} /><input name="q" placeholder="Search doctors or specialities" aria-label="Search doctors" />
              </form>
            )}
            <div className="top-date"><small>Today</small><b>{new Date().toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })}</b></div>
          </div>
        </div>
        {profile === null && (
          <div className="banner">
            <span>{doctor ? 'Add your profile so patients can find and book you.' : 'Complete your profile before booking your first appointment.'}</span>
            <Link to="/profile">Complete profile</Link>
          </div>
        )}
        <Outlet />
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem('clinexa_user')); } catch { return null; } });
  const [profile, setProfile] = useState(undefined);
  const [isAdmin, setIsAdmin] = useState(null);
  const [toast, setToast] = useState('');
  const notify = useCallback((m) => { setToast(m); setTimeout(() => setToast(''), 3200); }, []);
  const loadProfile = useCallback(async () => {
    if (!user) return;
    try { setProfile(await api.profile(user.role)); } catch (e) { setProfile(e.status === 404 ? null : undefined); }
  }, [user]);
  useEffect(() => { loadProfile(); }, [loadProfile]);
  useEffect(() => {
    if (!user) {
      setIsAdmin(false);
      return undefined;
    }
    let active = true;
    setIsAdmin(null);
    api.adminAccess()
      .then(({ is_admin }) => { if (active) setIsAdmin(is_admin); })
      .catch((error) => {
        if (!active) return;
        setIsAdmin(false);
        notify(`Admin access could not be checked: ${error.message}`);
      });
    return () => { active = false; };
  }, [user, notify]);
  const signIn = (u) => { localStorage.setItem('clinexa_user', JSON.stringify(u)); setUser(u); };
  const signOut = () => { tokenStore.clear(); setUser(null); setProfile(undefined); setIsAdmin(false); };

  return (
    <Ctx.Provider value={{ user, profile, isAdmin, loadProfile, notify, signIn, signOut }}>
      {user ? (
        <Routes>
          <Route element={<Shell />}>
            <Route index element={user.role === 'Doctor' ? <DoctorHome /> : <Overview />} />
            <Route path="doctors" element={<Doctors />} />
            <Route path="appointments" element={user.role === 'Doctor' ? <DoctorHome /> : <Appointments />} />
            <Route path="records" element={<Records />} />
            <Route path="profile" element={<Profile />} />
            <Route path="admin/doctors" element={isAdmin === null ? <Loading /> : isAdmin ? <AddDoctorProfile /> : <Navigate to="/" replace />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      ) : (
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Auth />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
      {toast && <div className="toast" role="status">{toast}</div>}
    </Ctx.Provider>
  );
}
