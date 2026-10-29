import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Heart, Brain, Bone, Baby, Eye, Smile, Stethoscope, Activity, CheckCircle2, BellRing, FileText, CalendarCheck, HeartPulse, ShieldCheck, UserRound, BriefcaseMedical, ArrowUpRight, Mail, LockKeyhole, Sparkles } from 'lucide-react';
import { api, tokenStore } from './api';
import { useApp } from './ctx';
import { Logo, Pulse } from './ui';

const SPECS = [[Heart, 'Cardiology', 'Heart and blood pressure'], [Brain, 'Neurology', 'Head, nerves and migraines'], [Bone, 'Orthopedics', 'Bones, joints and sports injuries'], [Baby, 'Pediatrics', 'Care for children'], [Eye, 'Ophthalmology', 'Eye checks and vision'], [Smile, 'Dentistry', 'Teeth and gum care'], [Stethoscope, 'General physician', 'Everyday health concerns'], [Activity, 'Dermatology', 'Skin, hair and nails']];

export function Landing() {
  return (
    <div>
      <div className="wrap">
        <div className="lnav">
          <Logo />
          <nav aria-label="Sections"><a href="#specialities">Specialities</a><a href="#how">How it works</a><a href="#doctors">For doctors</a></nav>
          <div className="acts"><Link to="/login" className="btn ghost">Sign in</Link><Link to="/login?mode=register" className="btn">Get started</Link></div>
        </div>
        <section className="lhero">
          <div>
            <h1>See the right doctor, <em>without the waiting room.</em></h1>
            <p className="lead">Search specialists, pick a time that is actually free, and keep your records and prescriptions in one place.</p>
            <div className="cta">
              <Link to="/login?mode=register" className="btn lg">Book an appointment</Link>
              <Link to="/login?mode=register&role=Doctor" className="btn ghost lg">I am a doctor</Link>
            </div>
            <div className="trust">
              <span><CheckCircle2 size={18} />Live availability</span>
              <span><BellRing size={18} />Reminder 1 hour before</span>
              <span><FileText size={18} />Records in one place</span>
            </div>
          </div>
          <div className="mock" aria-hidden="true">
            <div className="blob"><Pulse className="pulse" /></div>
            <div className="float f1">
              <div className="row"><div className="doc-av c1" style={{ width: 46, height: 46, borderRadius: 14 }}><Stethoscope size={22} /></div><div><b>Cardiology</b><div className="muted" style={{ fontSize: '.85rem' }}>City Heart Clinic</div></div></div>
              <div className="slots"><span className="slot">10:00 AM</span><span className="slot" style={{ background: 'var(--blue)', color: '#fff', borderColor: 'var(--blue)' }}>10:30 AM</span><span className="slot">11:00 AM</span></div>
            </div>
            <div className="float f2"><div className="lbl muted" style={{ fontWeight: 600 }}>Appointment booked</div><div style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-.03em' }}>Tomorrow, 10:30 AM</div><span className="pill confirmed" style={{ marginTop: '.4rem' }}><i />Confirmed</span></div>
            <div className="float f3"><div className="ico mint"><BellRing size={18} /></div><b style={{ fontSize: '.9rem' }}>Reminder sent</b></div>
          </div>
        </section>
      </div>
      <section className="sec" id="specialities"><div className="wrap">
        <div className="sec-head"><h2>Find care for what you need</h2><p>Browse by speciality, then see who has time this week.</p></div>
        <div className="specs">
          {SPECS.map(([Icon, name, text], i) => (
            <Link to="/login?mode=register" className="spec" key={name}><div className={`doc-av c${i % 5}`} style={{ width: 48, height: 48, borderRadius: 14 }}><Icon size={22} /></div><div><h3>{name}</h3><p className="muted" style={{ fontSize: '.88rem' }}>{text}</p></div></Link>
          ))}
        </div>
      </div></section>
      <section className="sec" id="how" style={{ paddingTop: 0 }}><div className="wrap">
        <div className="sec-head"><h2>Booked in three steps</h2></div>
        <div className="steps">
          {[['1', 'Find a doctor', 'Search by speciality or name and compare experience, location and fees.'], ['2', 'Pick a time', 'Choose from the slots the doctor has opened. Booked times never show up twice.'], ['3', 'Show up prepared', 'Get a reminder before your visit, then find your diagnosis and prescription afterwards.']].map(([n, t, p]) => (
            <div className="step" key={n}><b>Step {n}</b><h3>{t}</h3><p>{p}</p></div>
          ))}
        </div>
      </div></section>
      <section className="sec" id="doctors" style={{ paddingTop: 0 }}><div className="wrap">
        <div className="dband">
          <div>
            <h2>Run your schedule your way</h2>
            <p style={{ color: '#C6D2EC', margin: '.8rem 0 1.6rem' }}>Set your hours once. Clinexa turns them into bookable slots and keeps your day organised.</p>
            <Link to="/login?mode=register&role=Doctor" className="btn light lg">Create a doctor account</Link>
          </div>
          <ul>
            {['Weekly working hours with your own slot length', 'Day-specific overrides for leave or extra clinics', 'Every patient booking in one clear list', 'Notes and prescriptions linked to each visit'].map((t) => <li key={t}><CalendarCheck size={18} />{t}</li>)}
          </ul>
        </div>
      </div></section>
      <div className="wrap"><div className="foot"><Logo /><span>Clinexa is a healthcare platform and does not replace medical advice.</span></div></div>
    </div>
  );
}

export function Auth() {
  const { signIn } = useApp();
  const [sp] = useSearchParams();
  const [mode, setMode] = useState(sp.get('mode') === 'register' ? 'register' : 'login');
  const [role, setRole] = useState(sp.get('role') === 'Doctor' ? 'Doctor' : 'Patient');
  const [f, setF] = useState({ name: '', email: '', password: '' });
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault(); setErr(''); setBusy(true);
    try {
      if (mode === 'register') await api.register({ name: f.name.trim(), email: f.email.trim(), password: f.password, role });
      const { access_token } = await api.login(f.email.trim(), f.password);
      tokenStore.set(access_token);
      const detected = mode === 'register' ? role : await api.detectRole();
      signIn({ email: f.email.trim(), role: detected, name: f.name.trim() || f.email.split('@')[0] });
    } catch (x) { tokenStore.clear(); setErr(x.message); } finally { setBusy(false); }
  };

  return (
    <main className={`auth-page ${mode === 'register' ? 'is-signup' : 'is-login'}`}>
      <section className="auth-story">
        <div className="auth-story-top">
          <Link to="/" aria-label="Clinexa home"><Logo light /></Link>
          <span className="auth-secure"><ShieldCheck size={15} /> Private and secure</span>
        </div>
        <div className="auth-story-content">
          <div className="auth-kicker"><HeartPulse size={15} /> YOUR HEALTH, IN GOOD HANDS</div>
          <h1>{mode === 'login' ? <>Care that keeps<br />you <em>connected.</em></> : <>A better way to<br />take care of <em>you.</em></>}</h1>
          <p>{mode === 'login'
            ? 'Your appointments, care team and health records—right where you need them.'
            : 'Join a thoughtful care experience that makes every next step feel simpler.'}</p>
          <div className="auth-preview" aria-hidden="true">
            <div className="auth-preview-head"><span className="auth-preview-icon"><Activity size={18} /></span><span><b>Your care, all in one place</b><small>Designed around you</small></span><ArrowUpRight size={17} /></div>
            <div className="auth-preview-rule" />
            <div className="auth-preview-points">
              <span><CheckCircle2 size={15} /> Find trusted specialists</span>
              <span><CheckCircle2 size={15} /> Manage visits with ease</span>
              <span><CheckCircle2 size={15} /> Keep your records close</span>
            </div>
          </div>
        </div>
        <div className="auth-story-foot"><span>© 2026 Clinexa</span><span><ShieldCheck size={14} /> Your health information stays protected</span></div>
        <div className="auth-orbit auth-orbit-one" />
        <div className="auth-orbit auth-orbit-two" />
      </section>

      <section className="auth-main">
        <div className="auth-main-top">
          <span>{mode === 'login' ? 'New to Clinexa?' : 'Already have an account?'}</span>
          <button type="button" className="auth-switch" onClick={() => { setErr(''); setMode(mode === 'login' ? 'register' : 'login'); }}>
            {mode === 'login' ? 'Create account' : 'Sign in'} <ArrowUpRight size={15} />
          </button>
        </div>
        <div className="auth-form-wrap">
          <div className="auth-heading">
            <span className="auth-heading-icon">{mode === 'login' ? <HeartPulse size={20} /> : <Sparkles size={19} />}</span>
            <div className="auth-eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'GET STARTED'}</div>
            <h2>{mode === 'login' ? 'Sign in to your account' : 'Create your account'}</h2>
            <p>{mode === 'login' ? 'Enter your details to continue your care journey.' : 'It only takes a moment to get started.'}</p>
          </div>

          <form onSubmit={submit} className="auth-form">
            {mode === 'register' && (
              <>
                <div className="auth-label-row"><span className="auth-label">I’m joining as a</span><span className="auth-step">STEP 1 OF 2</span></div>
                <div className="role-picker" role="group" aria-label="Choose account type">
                  {[['Patient', UserRound, 'I’m looking for care'], ['Doctor', BriefcaseMedical, 'I provide care']].map(([r, Icon, description]) => (
                    <button className="role-option" type="button" key={r} aria-pressed={role === r} onClick={() => setRole(r)}>
                      <span className="role-icon"><Icon size={19} /></span>
                      <span className="role-copy"><b>{r}</b><small>{description}</small></span>
                      <span className="role-radio" />
                    </button>
                  ))}
                </div>
                <div className="field auth-field">
                  <label htmlFor="n">Full name</label>
                  <div className="auth-input-wrap"><UserRound size={17} /><input id="n" required value={f.name} onChange={set('name')} autoComplete="name" placeholder="How should we address you?" /></div>
                </div>
              </>
            )}
            <div className="field auth-field">
              <label htmlFor="e">Email address</label>
              <div className="auth-input-wrap"><Mail size={17} /><input id="e" type="email" required value={f.email} onChange={set('email')} autoComplete="email" placeholder="you@example.com" /></div>
            </div>
            <div className="field auth-field">
              <label htmlFor="p">Password</label>
              <div className="auth-input-wrap"><LockKeyhole size={17} /><input id="p" type="password" required minLength={mode === 'register' ? 8 : undefined} pattern={mode === 'register' ? '(?=.*[A-Z])(?=.*[0-9]).*' : undefined} title={mode === 'register' ? 'Use at least 8 characters, including an uppercase letter and a number.' : undefined} value={f.password} onChange={set('password')} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder={mode === 'register' ? '8+ characters, one uppercase letter and one number' : 'Enter your password'} /></div>
            </div>
            {mode === 'login' && <div className="auth-form-meta"><span><ShieldCheck size={14} /> Secure sign-in</span></div>}
            {err && <div className="err" role="alert">{err}</div>}
            <button className="btn lg auth-submit" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in securely' : 'Create my account'}<ArrowUpRight size={17} /></button>
            {mode === 'register' && <p className="auth-terms">By creating an account, you agree to use Clinexa responsibly. Your health information is only shared to support your care.</p>}
          </form>
          <div className="auth-help"><span>Need help?</span> <a href="mailto:support@clinexa.health">Contact our support team</a></div>
        </div>
      </section>
    </main>
  );
}
