export async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Cannot reach the backend. Start FastAPI on port 8000, then try again.');
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => `${item.loc?.slice(1).join(' ')}: ${item.msg}`).join('; ')
      : data.detail;
    throw new Error(detail || `The request failed (${response.status}). Please try again.`);
  }
  return response.status === 204 ? null : response.json();
}

export function exportUrl(id, format, scope = 'lesson') {
  return `/api/lessons/${encodeURIComponent(id)}/export?format=${format}&scope=${scope}`;
}

export async function downloadExport(id, format, scope = 'lesson') {
  const response = await fetch(exportUrl(id, format, scope));
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Export failed. Please try again.');
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const filename = response.headers.get('content-disposition')?.match(/filename="?([^";]+)"?/)?.[1];
  link.href = url;
  link.download = filename || `lessonforge-${scope}.${format === 'markdown' ? 'md' : format}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
