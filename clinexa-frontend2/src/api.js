const BASE = 'https://clinexa-pauo.onrender.com' || '/api';

export const tokenStore = {
  get: () => localStorage.getItem('clinexa_token'),
  set: (t) => localStorage.setItem('clinexa_token', t),
  clear: () => {
    localStorage.removeItem('clinexa_token');
    localStorage.removeItem('clinexa_user');
  },
};

async function req(path, { method = 'GET', body, form } = {}) {
  const headers = {};
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  let data;
  if (form) data = new URLSearchParams(form);
  else if (body) {
    headers['Content-Type'] = 'application/json';
    data = JSON.stringify(body);
  }
  const res = await fetch(BASE + path, { method, headers, body: data });
  if (res.status === 401 && token) {
    tokenStore.clear();
    window.location.href = '/login';
  }
  if (res.status === 204) return null;
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    const d = json?.detail;
    const err = new Error(
      typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x.msg).join(', ') : `Something went wrong (${res.status})`,
    );
    err.status = res.status;
    throw err;
  }
  return json;
}

const profilePath = (role) => (role === 'Doctor' ? '/doctor/profile/' : '/patient/profile/');

export const api = {
  login: (email, password) => req('/login', { method: 'POST', form: { username: email, password } }),
  register: (b) => req('/register', { method: 'POST', body: b }),
  // The API has no "who am I" endpoint: a doctor gets 403 on the patient profile route.
  detectRole: async () => {
    try {
      await req('/patient/profile/');
      return 'Patient';
    } catch (e) {
      return e.status === 403 ? 'Doctor' : 'Patient';
    }
  },
  profile: (role) => req(profilePath(role)),
  saveProfile: (role, body, exists) => req(profilePath(role), { method: exists ? 'PATCH' : 'POST', body }),
  adminAccess: () => req('/doctor/profile/admin/access'),
  doctorsWithoutProfiles: () => req('/doctor/profile/admin/accounts'),
  createDoctorProfile: (userId, body) => req(`/doctor/profile/admin/accounts/${userId}/profile`, { method: 'POST', body }),
  doctorsBySpec: (s) => req(`/doctor/profile/search/specialisation/${encodeURIComponent(s)}`),
  doctorsByName: (n) => req(`/doctor/profile/search/name/${encodeURIComponent(n)}`),
  slots: (id, date) => req(`/doctors/${id}/available-slots?target_date=${date}`),
  book: (b) => req('/appointments/', { method: 'POST', body: b }),
  myAppointments: (view) => req(`/appointments/patient?page_size=50${view ? `&view=${view}` : ''}`),
  doctorAppointments: () => req('/appointments/doctor?page_size=100'),
  cancel: (id) => req(`/appointments/${id}/cancel`, { method: 'PATCH' }),
  records: () => req('/medicalreport/patient'),
  prescriptions: () => req('/prescription/patient'),
};
