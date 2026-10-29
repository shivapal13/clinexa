const BASE = import.meta.env.VITE_API_URL || 'https://clinexa-pauo.onrender.com';

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
      if (e.status === 403) return 'Doctor';
      throw e;
    }
  },
  getProfile: (role) => req(profilePath(role)),
  createProfile: (role, body) => req(profilePath(role), { method: 'POST', body }),
  updateProfile: (role, body) => req(profilePath(role), { method: 'PATCH', body }),

  // Patient flows
  getAvailableSlots: (doctorId, date) => req(`/doctors/${doctorId}/available-slots?target_date=${date}`),
  bookAppointment: (b) => req('/appointments/', { method: 'POST', body: b }),
  getPatientAppointments: (view, page = 1) =>
    req(`/appointments/patient?page=${page}&page_size=10${view ? `&view=${view}` : ''}`),
  cancelPatientAppointment: (id) => req(`/appointments/${id}/cancel`, { method: 'PATCH' }),
  rescheduleAppointment: (id, b) => req(`/appointments/${id}`, { method: 'PATCH', body: b }),
  searchDoctors: (name) => req(`/doctor/profile/search/name/${encodeURIComponent(name)}`),
  getDoctorById: (id) => req(`/doctor/profile/${id}`),
  getPatientRecords: () => req('/medicalreport/patient'),
  getPatientPrescriptions: () => req('/prescription/patient'),

  // Doctor flows
  getDoctorAppointments: (status, date, page = 1) => {
    const params = new URLSearchParams({ page, page_size: 10 });
    if (status) params.set('status', status);
    if (date) params.set('appointment_date', date);
    return req(`/appointments/doctor?${params}`);
  },
  updateAppointmentStatus: (id, status) => req(`/appointments/${id}/status`, { method: 'PATCH', body: { status } }),
  cancelDoctorAppointment: (id) => req(`/appointments/${id}/doctor-cancel`, { method: 'PATCH' }),
  getDoctorRecords: () => req('/medicalreport/doctor'),
  createRecord: (apptId, body) => req(`/medicalreport/${apptId}`, { method: 'POST', body }),
  getDoctorPrescriptions: () => req('/prescription/doctor'),
  createPrescription: (recId, body) => req(`/prescription/${recId}`, { method: 'POST', body }),

  // Doctor availability management
  getRecurring: () => req('/doctor/availability/'),
  createRecurring: (body) => req('/doctor/availability/', { method: 'POST', body }),
  deleteRecurring: (id) => req(`/doctor/availability/${id}`, { method: 'DELETE' }),
  getOverrides: () => req('/doctor/availability/override/'),
  createOverride: (body) => req('/doctor/availability/override/', { method: 'POST', body }),
  deleteOverride: (id) => req(`/doctor/availability/override/${id}`, { method: 'DELETE' }),

  // Admin flows
  getAdminAccess: () => req('/doctor/profile/admin/access'),
  getAdminDoctorAccounts: () => req('/doctor/profile/admin/accounts'),
  createDoctorProfileForAccount: (userId, body) =>
    req(`/doctor/profile/admin/accounts/${userId}/profile`, { method: 'POST', body }),
  getPendingDoctorReviews: () => req('/doctor/profile/admin/pending'),
  reviewDoctorProfile: (doctorId, verification_status) =>
    req(`/doctor/profile/admin/${doctorId}/verification`, {
      method: 'PATCH',
      body: { verification_status },
    }),
};
