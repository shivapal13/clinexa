import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Stethoscope, Search, MapPin, Clock, X, CalendarCheck, CalendarClock, History, Pill, ClipboardList, Users, CalendarX2, ArrowRight, HeartPulse, ShieldCheck, Sparkles, CalendarPlus, FileHeart } from 'lucide-react';
import { api } from './api';
import { useApp } from './ctx';
import { iso, parse, fmtDate, fmtTime, when, or404, useLoad, Status, Loading, Note, Stat, Head, Calendar, Pulse } from './ui';

const DateBox = ({ d }) => <div className="datebox"><b>{parse(d).getDate()}</b><span>{parse(d).toLocaleDateString('en-IN', { month: 'short' })}</span></div>;
const count = (r) => (r.status === 'fulfilled' ? (r.value?.appointments?.length ?? r.value?.length ?? 0) : '–');

export function Overview() {
  const { user } = useApp();
  const { data, error, loading, reload } = useLoad(() => Promise.allSettled([api.myAppointments('UPCOMING'), api.myAppointments('HISTORY'), or404(api.prescriptions())]), []);
  const hr = new Date().getHours();
  const greet = hr < 12 ? 'Good morning' : hr < 17 ? 'Good afternoon' : 'Good evening';
  const up = data?.[0].status === 'fulfilled' ? data[0].value.appointments.filter((a) => a.status !== 'CANCELLED') : [];
  const failed = data && data[0].status === 'rejected' ? data[0].reason : error;
  const [next, ...rest] = up;
  return (
    <div className="patient-dashboard">
      <header className="dashboard-welcome">
        <div>
          <div className="dashboard-kicker"><Sparkles size={15} /> YOUR PERSONAL CARE SPACE</div>
          <h1>{greet}, {user.name.split(' ')[0]}<span className="welcome-wave">.</span></h1>
          <p>Keep track of your care and take your next step with confidence.</p>
        </div>
        <Link to="/doctors" className="btn dashboard-book"><CalendarPlus size={17} /> Book an appointment</Link>
      </header>

      <div className="dashboard-stats">
        <Stat icon={CalendarClock} tone="blue" value={loading ? '–' : failed ? '–' : up.length} label="Upcoming visits" />
        <Stat icon={History} tone="mint" value={loading ? '–' : count(data[1])} label="Past visits" />
        <Stat icon={Pill} tone="amber" value={loading ? '–' : count(data[2])} label="Active prescriptions" />
      </div>

      {loading ? <Loading /> : failed ? (
        <Note icon={CalendarX2} title="We could not load your appointments" text={failed.message} onRetry={reload} />
      ) : (
        <div className="dashboard-grid">
          <div className="dashboard-main">
            <section className={`next-visit-card${next ? '' : ' is-empty'}`}>
              <div className="next-visit-copy">
                <div className="next-visit-label"><span className="live-dot" /> {next ? 'YOUR NEXT APPOINTMENT' : 'YOUR CARE JOURNEY'}</div>
                <h2>{next ? `${when(next.appointment_date)}, ${fmtTime(next.appointment_time)}` : 'A good time to find care'}</h2>
                <p>{next ? `${next.specialisation} · ${fmtDate(next.appointment_date)}` : 'Find the right specialist and choose a time that works for you.'}</p>
                {next && <div className="next-visit-meta"><span><CalendarCheck size={15} />{next.medical_service}</span><Status s={next.status} /></div>}
                <Link to={next ? '/appointments' : '/doctors'} className="next-visit-link">
                  {next ? 'View appointment details' : 'Explore doctors'} <ArrowRight size={16} />
                </Link>
              </div>
              <div className="next-visit-art" aria-hidden="true">
                <div className="visit-art-orbit visit-art-orbit-a" />
                <div className="visit-art-orbit visit-art-orbit-b" />
                <div className="visit-art-icon"><HeartPulse size={43} strokeWidth={1.5} /></div>
                <Pulse className="visit-art-pulse" />
                <span className="visit-art-check"><ShieldCheck size={16} /></span>
              </div>
            </section>

            <section className="dashboard-section">
              <div className="dashboard-section-head">
                <div><h2>Upcoming visits</h2><p>Your scheduled appointments at a glance.</p></div>
                <Link to="/appointments" className="dashboard-text-link">See all <ArrowRight size={15} /></Link>
              </div>
              {up.length === 0 ? (
                <div className="dashboard-empty">
                  <span className="dashboard-empty-icon"><CalendarCheck size={21} /></span>
                  <div><b>No upcoming visits</b><p>Your scheduled appointments will show up here.</p></div>
                  <Link to="/doctors" className="btn ghost">Find a doctor</Link>
                </div>
              ) : (
                <div className="dashboard-visit-list">
                  {up.slice(0, 4).map((a) => (
                    <div className="dashboard-visit" key={a.appointment_id}>
                      <DateBox d={a.appointment_date} />
                      <div className="dashboard-visit-info"><h3>{a.specialisation}</h3><p>{a.medical_service} <span>·</span> {fmtTime(a.appointment_time)}</p></div>
                      <Status s={a.status} />
                      <Link to="/appointments" className="dashboard-visit-arrow" aria-label="View appointment"><ArrowRight size={17} /></Link>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="care-prompt">
              <span className="care-prompt-icon"><FileHeart size={20} /></span>
              <div><b>Your health records, together</b><p>Find visit summaries and prescriptions in your health records.</p></div>
              <Link to="/records" className="dashboard-text-link">View records <ArrowRight size={15} /></Link>
            </section>
          </div>

          <aside className="dashboard-aside">
            <section className="dashboard-panel calendar-panel">
              <div className="dashboard-section-head"><div><h2>Your calendar</h2><p>Appointments this month</p></div></div>
              <Calendar marked={new Set(up.map((a) => a.appointment_date))} />
              <div className="calendar-legend"><span /> Scheduled visit</div>
            </section>
            <section className="dashboard-panel specialty-panel">
              <div className="dashboard-section-head"><div><h2>Explore specialties</h2><p>Start with what you need.</p></div></div>
              <div className="specialty-list">
                {['Cardiology', 'Dermatology', 'Pediatrics', 'Neurology', 'Orthopedics'].map((s, i) => (
                  <Link key={s} to={`/doctors?q=${s}`} className="specialty-link">
                    <span className={`specialty-dot tone-${i}`}><Stethoscope size={15} /></span><span>{s}</span><ArrowRight size={15} />
                  </Link>
                ))}
              </div>
            </section>
          </aside>
        </div>
      )}
    </div>
  );
}

const SPECS = ['Cardiology', 'Dermatology', 'Pediatrics', 'Neurology', 'Orthopedics', 'General physician'];

export function Doctors() {
  const [sp] = useSearchParams();
  const [q, setQ] = useState(sp.get('q') || '');
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [pick, setPick] = useState(null);

  const find = async (term) => {
    setBusy(true); setError('');
    try {
      let r = await or404(api.doctorsBySpec(term));
      if (r.length === 0) r = await or404(api.doctorsByName(term));
      setRes(r);
    } catch (e) { setError(e.message); setRes(null); } finally { setBusy(false); }
  };
  useEffect(() => { const t = sp.get('q'); if (t) { setQ(t); find(t); } }, [sp]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <Head title="Find a doctor" text="Search by speciality or doctor name, then pick a time." />
      <form className="finder" onSubmit={(e) => { e.preventDefault(); if (q.trim()) find(q.trim()); }}>
        <label className="tsearch"><Search size={18} /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="For example, Cardiology" aria-label="Search doctors" /></label>
        <button className="btn" disabled={busy}>Search</button>
      </form>
      <div className="quick" style={{ marginBottom: '1.5rem' }}>{SPECS.map((s) => <button key={s} className="chip" onClick={() => { setQ(s); find(s); }}>{s}</button>)}</div>
      {error && <div className="err" role="alert" style={{ marginBottom: '1rem' }}>{error}</div>}
      {busy ? <Loading /> : res && (res.length === 0
        ? <Note icon={Users} title="No doctors found" text="Try another speciality or a shorter search term." />
        : <div className="grid2">{res.map((d) => (
            <article className="doc" key={d.doctor_id}>
              <div className="doc-top">
                <div className={`doc-av c${d.doctor_id % 5}`}><Stethoscope size={28} /></div>
                <div><h3>{d.specialisation}</h3><p className="muted">{d.hospital_name}</p></div>
              </div>
              <div className="facts"><span className="fact"><MapPin size={14} />{d.city}</span><span className="fact"><Clock size={14} />{d.experience} years</span></div>
              <div className="doc-foot"><div><b>₹{d.fees}</b><small>per consultation</small></div><button className="btn" onClick={() => setPick(d)}>Book visit</button></div>
            </article>))}</div>)}
      {pick && <Book doc={pick} onClose={() => setPick(null)} />}
    </>
  );
}

const SERVICES = ['General consultation', 'Follow-up', 'Health check-up', 'Second opinion'];

function Book({ doc, onClose }) {
  const { notify, profile } = useApp();
  const days = Array.from({ length: 10 }, (_, i) => { const d = new Date(); d.setDate(d.getDate() + i); return d; });
  const [date, setDate] = useState(iso(days[0]));
  const [slots, setSlots] = useState(null);
  const [slot, setSlot] = useState('');
  const [service, setService] = useState(SERVICES[0]);
  const [reason, setReason] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let live = true;
    setSlots(null); setSlot('');
    api.slots(doc.doctor_id, date).then((r) => live && setSlots(r.available_slots), () => live && setSlots([]));
    return () => { live = false; };
  }, [doc.doctor_id, date]);
  useEffect(() => {
    const k = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', k);
    return () => window.removeEventListener('keydown', k);
  }, [onClose]);

  const now = new Date();
  const future = (slots || []).filter((s) => date !== iso(now) || s.start_time > `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`);
  const groups = [['Morning', (h) => h < 12], ['Afternoon', (h) => h >= 12 && h < 17], ['Evening', (h) => h >= 17]];

  const submit = async () => {
    if (!slot) return setErr('Choose a time slot first.');
    setBusy(true); setErr('');
    try {
      await api.book({ doctor_id: doc.doctor_id, appointment_date: date, appointment_time: slot, medical_service: service, reason: reason.trim() || service });
      notify('Appointment booked'); onClose();
    } catch (x) { setErr(x.message); } finally { setBusy(false); }
  };

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={`Book ${doc.specialisation}`}>
        <div className="drawer-body">
          <div className="doc-top" style={{ justifyContent: 'space-between' }}>
            <div className="doc-top"><div className={`doc-av c${doc.doctor_id % 5}`}><Stethoscope size={28} /></div><div><h2>{doc.specialisation}</h2><p className="muted">{doc.hospital_name}, {doc.city}</p></div></div>
            <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={20} /></button>
          </div>
          {profile === null && <div className="banner" style={{ margin: 0 }}>Complete your profile to book. <Link to="/profile">Go to profile</Link></div>}
          <div className="field"><span className="lbl">Choose a day</span>
            <div className="days">{days.map((d) => <button key={iso(d)} className="dchip" aria-pressed={date === iso(d)} onClick={() => setDate(iso(d))}><small>{d.toLocaleDateString('en-IN', { weekday: 'short' })}</small><b>{d.getDate()}</b></button>)}</div>
          </div>
          <div className="field"><span className="lbl">Available times</span>
            {slots === null ? <p className="muted">Checking availability…</p> : future.length === 0 ? <p className="muted">No times left on this day. Try another date.</p> : groups.map(([name, test]) => {
              const g = future.filter((s) => test(+s.start_time.split(':')[0]));
              return g.length > 0 && <div className="slot-group" key={name}><h4>{name}</h4><div className="slots">{g.map((s) => <button key={s.start_time} className="slot" aria-pressed={slot === s.start_time} onClick={() => setSlot(s.start_time)}>{fmtTime(s.start_time)}</button>)}</div></div>;
            })}
          </div>
          <div className="field"><span className="lbl">Type of visit</span><div className="quick">{SERVICES.map((s) => <button key={s} className="chip" aria-pressed={service === s} onClick={() => setService(s)} style={service === s ? { background: 'var(--blue)', color: '#fff' } : undefined}>{s}</button>)}</div></div>
          <div className="field"><label htmlFor="r">What would you like to discuss?</label><textarea id="r" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Symptoms or questions for the doctor" /></div>
        </div>
        <div className="drawer-foot">
          {err && <div className="err" role="alert">{err}</div>}
          <button className="btn lg" onClick={submit} disabled={busy}>{busy ? 'Booking…' : slot ? `Confirm ${fmtDate(date)}, ${fmtTime(slot)}` : 'Confirm booking'}</button>
        </div>
      </aside>
    </>
  );
}

export function Appointments() {
  const [tab, setTab] = useState('UPCOMING');
  const { data, error, loading, reload } = useLoad(() => api.myAppointments(tab), [tab]);
  const list = data?.appointments || [];
  return (
    <>
      <Head title="Your visits" text="Everything you have booked, past and upcoming." />
      <div className="tabs">{[['UPCOMING', 'Upcoming'], ['HISTORY', 'History']].map(([k, l]) => <button key={k} aria-pressed={tab === k} onClick={() => setTab(k)}>{l}</button>)}</div>
      {loading ? <Loading /> : error ? <Note icon={CalendarX2} title="We could not load your visits" text={error.message} onRetry={reload} />
        : list.length === 0 ? <Note icon={CalendarCheck} title={tab === 'UPCOMING' ? 'Nothing coming up' : 'No past visits yet'} text="Find a doctor to book your first visit.">{tab === 'UPCOMING' && <Link to="/doctors" className="btn">Find a doctor</Link>}</Note>
        : <div className="items">{list.map((a) => <VisitItem key={a.appointment_id} a={a} />)}</div>}
    </>
  );
}

export function DoctorHome() {
  const { notify } = useApp();
  const [filter, setFilter] = useState('ALL');
  const { data, error, loading, reload } = useLoad(() => api.doctorAppointments(), []);
  const all = data?.appointments || [];
  const list = all.filter((a) => filter === 'ALL' || a.status === filter);
  const cancel = async (id) => {
    if (!window.confirm('Cancel this appointment? The patient will see it as cancelled.')) return;
    try { await api.cancel(id); notify('Appointment cancelled'); reload(); } catch (e) { notify(e.message); }
  };
  return (
    <>
      <Head title="Your appointments" text="Patients who have booked time with you." />
      <div className="stats" style={{ marginBottom: '1.5rem' }}>
        <Stat icon={CalendarClock} tone="blue" value={all.filter((a) => a.appointment_date === iso(new Date()) && a.status !== 'CANCELLED').length} label="Today" />
        <Stat icon={ClipboardList} tone="amber" value={all.filter((a) => a.status === 'PENDING').length} label="Pending" />
        <Stat icon={Users} tone="mint" value={all.length} label="Total bookings" />
      </div>
      <div className="tabs">{[['ALL', 'All'], ['PENDING', 'Pending'], ['CONFIRMED', 'Confirmed'], ['CANCELLED', 'Cancelled']].map(([k, l]) => <button key={k} aria-pressed={filter === k} onClick={() => setFilter(k)}>{l}</button>)}</div>
      {loading ? <Loading /> : error ? <Note icon={CalendarX2} title="We could not load appointments" text={error.message} onRetry={reload} />
        : list.length === 0 ? <Note icon={CalendarCheck} title="No appointments here" text="New bookings will appear as patients schedule with you." />
        : <div className="items">{list.map((a) => (
            <div className="item" key={a.appointment_id}>
              <DateBox d={a.appointment_date} />
              <div><h3>{a.medical_service} at {fmtTime(a.appointment_time)}</h3><p className="muted">Patient #{a.patient_id}: {a.reason}</p></div>
              <div className="end"><Status s={a.status} />{['PENDING', 'CONFIRMED'].includes(a.status) && <button className="btn danger sm" onClick={() => cancel(a.appointment_id)}>Cancel</button>}</div>
            </div>))}</div>}
    </>
  );
}

export function Records() {
  const recs = useLoad(() => or404(api.records()), []);
  const rx = useLoad(() => or404(api.prescriptions()), []);
  return (
    <>
      <Head title="Health records" text="Diagnoses, notes and prescriptions from your doctors." />
      <div className="cols" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))' }}>
        <section>
          <div className="card-title"><h2>Visit summaries</h2></div>
          {recs.loading ? <Loading /> : recs.error ? <Note icon={ClipboardList} title="We could not load your records" text={recs.error.message} onRetry={recs.reload} />
            : recs.data.length === 0 ? <Note icon={ClipboardList} title="No records yet" text="Summaries appear after a doctor completes a visit." />
            : <div className="items">{recs.data.map((r) => (
                <div className="card rec" key={r.record_id}><div className="ico blue"><ClipboardList size={20} /></div><h3>{r.diagnosis}</h3><p className="muted">Symptoms: {r.symptoms}</p>{r.doctor_notes && <p>{r.doctor_notes}</p>}{r.follow_up_dates && <span className="fact" style={{ justifySelf: 'start' }}>Follow-up {fmtDate(r.follow_up_dates)}</span>}</div>))}</div>}
        </section>
        <section>
          <div className="card-title"><h2>Prescriptions</h2></div>
          {rx.loading ? <Loading /> : rx.error ? <Note icon={Pill} title="We could not load your prescriptions" text={rx.error.message} onRetry={rx.reload} />
            : rx.data.length === 0 ? <Note icon={Pill} title="No prescriptions" text="Medicines your doctor prescribes will be listed here." />
            : <div className="items">{rx.data.map((p) => (
                <div className="card rec" key={p.prescription_id}><div className="ico amber"><Pill size={20} /></div><h3>{p.medicine_name}</h3><p className="muted">{p.dosage}, {p.frequency}, for {p.duration}</p>{p.instructions && <p>{p.instructions}</p>}</div>))}</div>}
        </section>
      </div>
    </>
  );
}

const FIELDS = {
  Patient: [['age', 'Age', 'number'], ['gender', 'Gender', ['Male', 'Female', 'Other']], ['blood_group', 'Blood group', ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']], ['phone_number', 'Phone number', 'tel'], ['address', 'Address', 'textarea']],
  Doctor: [['specialisation', 'Specialisation', 'text'], ['experience', 'Years of experience', 'number'], ['fees', 'Consultation fee (₹)', 'number'], ['city', 'City', 'text'], ['hospital_name', 'Hospital or clinic', 'text'], ['license_number', 'Professional license number', 'text'], ['bio', 'About you', 'textarea']],
};

export function Profile() {
  const { user, profile, loadProfile, notify } = useApp();
  const fields = FIELDS[user.role];
  const [f, setF] = useState({});
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => { setF(profile || {}); }, [profile]);

  const submit = async (e) => {
    e.preventDefault(); setErr(''); setBusy(true);
    const body = {};
    fields.forEach(([k, , t]) => { const v = f[k] ?? ''; body[k] = t === 'number' ? (k === 'fees' ? parseFloat(v) : parseInt(v, 10)) : v; });
    try { await api.saveProfile(user.role, body, !!profile); await loadProfile(); notify('Profile saved'); }
    catch (x) { setErr(x.message); } finally { setBusy(false); }
  };

  return (
    <>
      <Head title="Your profile" text={user.role === 'Doctor' ? 'This is what patients see when they search for you.' : 'Doctors use this to prepare for your visit.'} />
      {user.role === 'Doctor' && profile && (
        <div className={`verification-banner ${profile.verification_status === 'VERIFIED' ? 'verified' : ''}`}>
          <ShieldCheck size={19} />
          <div><b>{profile.verification_status === 'VERIFIED' ? 'Your profile is verified' : profile.verification_status === 'REJECTED' ? 'Your profile needs an update' : 'Your profile is under review'}</b><p>{profile.verification_status === 'VERIFIED' ? 'Patients can find your profile and book appointments.' : profile.verification_status === 'REJECTED' ? 'Update your professional license details and save your profile to submit it for review again.' : 'Add your professional license number. An administrator must review and approve your profile before patients can find or book you.'}</p></div>
        </div>
      )}
      <div className="profile">
        <div className="card who"><div className="avatar">{user.name[0]?.toUpperCase()}</div><h2>{user.name}</h2><p className="muted">{user.email}</p><span className="pill"><i />{user.role}</span></div>
        <form className="card form" onSubmit={submit}>
          {fields.map(([k, label, type]) => (
            <div className={`field${type === 'textarea' ? ' full' : ''}`} key={k}>
              <label htmlFor={k}>{label}</label>
              {Array.isArray(type) ? <select id={k} required value={f[k] ?? ''} onChange={(e) => setF({ ...f, [k]: e.target.value })}><option value="" disabled>Select</option>{type.map((o) => <option key={o}>{o}</option>)}</select>
                : type === 'textarea' ? <textarea id={k} rows={3} required value={f[k] ?? ''} onChange={(e) => setF({ ...f, [k]: e.target.value })} />
                : <input id={k} type={type} required min={type === 'number' ? 0 : undefined} step={k === 'fees' ? '0.01' : undefined} value={f[k] ?? ''} onChange={(e) => setF({ ...f, [k]: e.target.value })} />}
            </div>
          ))}
          {err && <div className="err full" role="alert">{err}</div>}
          <div className="full"><button className="btn lg" disabled={busy}>{busy ? 'Saving…' : 'Save profile'}</button></div>
        </form>
      </div>
    </>
  );
}

const EMPTY_DOCTOR_FORM = {
  specialisation: '',
  experience: '',
  fees: '',
  city: '',
  hospital_name: '',
  license_number: '',
  bio: '',
};

export function AddDoctorProfile() {
  const { notify } = useApp();
  const { data: accounts, error: loadError, loading, reload } = useLoad(() => api.doctorsWithoutProfiles(), []);
  const [accountId, setAccountId] = useState('');
  const [form, setForm] = useState(EMPTY_DOCTOR_FORM);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await api.createDoctorProfile(Number(accountId), {
        ...form,
        experience: Number(form.experience),
        fees: Number(form.fees),
      });
      setForm(EMPTY_DOCTOR_FORM);
      setAccountId('');
      notify('Doctor profile created and submitted for verification');
      reload();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Head title="Add a doctor profile" text="Create a profile for an existing doctor account. New profiles remain hidden from patients until verified." />
      {loading ? <Loading /> : loadError ? (
        <Note icon={ShieldCheck} title="Doctor accounts could not be loaded" text={loadError.message} onRetry={reload} />
      ) : accounts.length === 0 ? (
        <Note icon={Stethoscope} title="No doctor accounts need a profile" text="Create or register a Doctor account first. It will appear here once it has no profile." onRetry={reload} />
      ) : (
        <form className="card form admin-doctor-form" onSubmit={submit}>
          <div className="field full">
            <label htmlFor="doctor-account">Existing doctor account</label>
            <select id="doctor-account" required value={accountId} onChange={(event) => setAccountId(event.target.value)}>
              <option value="" disabled>Select a doctor account</option>
              {accounts.map((account) => <option key={account.user_id} value={account.user_id}>{account.name} · {account.email}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="doctor-specialisation">Specialisation</label>
            <input id="doctor-specialisation" required value={form.specialisation} onChange={(event) => setForm({ ...form, specialisation: event.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="doctor-experience">Years of experience</label>
            <input id="doctor-experience" type="number" min="0" step="1" required value={form.experience} onChange={(event) => setForm({ ...form, experience: event.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="doctor-fees">Consultation fee (₹)</label>
            <input id="doctor-fees" type="number" min="0" step="0.01" required value={form.fees} onChange={(event) => setForm({ ...form, fees: event.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="doctor-city">City</label>
            <input id="doctor-city" required value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} />
          </div>
          <div className="field full">
            <label htmlFor="doctor-hospital">Hospital or clinic</label>
            <input id="doctor-hospital" required value={form.hospital_name} onChange={(event) => setForm({ ...form, hospital_name: event.target.value })} />
          </div>
          <div className="field full">
            <label htmlFor="doctor-license">Professional license number</label>
            <input id="doctor-license" minLength="3" maxLength="128" required value={form.license_number} onChange={(event) => setForm({ ...form, license_number: event.target.value })} />
          </div>
          <div className="field full">
            <label htmlFor="doctor-bio">About the doctor</label>
            <textarea id="doctor-bio" rows={4} required value={form.bio} onChange={(event) => setForm({ ...form, bio: event.target.value })} />
          </div>
          {error && <div className="err full" role="alert">{error}</div>}
          <div className="full">
            <button className="btn lg" disabled={busy || !accountId}>{busy ? 'Creating profile…' : 'Create pending profile'}</button>
          </div>
        </form>
      )}
    </>
  );
}
