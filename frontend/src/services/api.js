const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function getJobs() {
  const response = await fetch(`${API_BASE_URL}/jobs`);
  if (!response.ok) throw new Error('Failed to fetch jobs');
  return response.json();
}

export async function createJob(title, description) {
  const response = await fetch(`${API_BASE_URL}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create job');
  }
  return response.json();
}

export async function getJob(jobId) {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
  if (!response.ok) throw new Error('Failed to fetch job details');
  return response.json();
}

export async function uploadCandidates(jobId, file, options = {}) {
  const { batchSize = 100, retrieveK = 100, explainTopN = 10, limit } = options;
  const formData = new FormData();
  formData.append('file', file);

  const url = new URL(`${API_BASE_URL}/candidates/upload`);
  url.searchParams.append('job_id', jobId);
  url.searchParams.append('batch_size', batchSize);
  url.searchParams.append('retrieve_k', retrieveK);
  url.searchParams.append('explain_top_n', explainTopN);
  if (limit !== undefined && limit !== null && limit !== '') {
    url.searchParams.append('limit', limit);
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload candidates');
  }
  return response.json();
}

export async function getUploadStatus() {
  const response = await fetch(`${API_BASE_URL}/candidates/status`);
  if (!response.ok) throw new Error('Failed to fetch upload status');
  return response.json();
}

export async function getLeaderboard(jobId, filterDisqualified = true) {
  const response = await fetch(
    `${API_BASE_URL}/rankings/${jobId}?filter_disqualified=${filterDisqualified}`
  );
  if (!response.ok) throw new Error('Failed to fetch leaderboard');
  return response.json();
}

export async function getCandidateDetails(jobId, candidateId) {
  const response = await fetch(
    `${API_BASE_URL}/rankings/${jobId}/candidate/${candidateId}`
  );
  if (!response.ok) throw new Error('Failed to fetch candidate details');
  return response.json();
}
