/* Frozen API access layer for the native frontend. */

export class ApiError extends Error {
  constructor(response, body) {
    super(body?.error?.message || `Request failed (${response.status})`);
    this.name = "ApiError";
    this.status = response.status;
    this.code = body?.error?.code || "HTTP_ERROR";
    this.category = body?.error?.category || "infrastructure";
    this.details = body?.error?.details || {};
  }
}

export class ApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
  }

  async request(path, options = {}) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { Accept: "application/json", ...(options.headers || {}) },
      ...options,
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new ApiError(response, body);
    return body;
  }

  runs() { return this.request("/api/runs"); }
  metrics(runId) { return this.request(`/api/runs/${encodeURIComponent(runId)}/metrics`); }
  videos() { return this.request("/api/videos"); }
  video(videoId) { return this.request(`/api/videos/${encodeURIComponent(videoId)}`); }
  trajectories() { return this.request("/api/trajectories"); }
  trajectory(trajectoryId) { return this.request(`/api/trajectories/${encodeURIComponent(trajectoryId)}`); }
  startTraining(config) { return this.request("/api/train/start", { method: "POST", body: JSON.stringify(config), headers: { "Content-Type": "application/json" } }); }
  trainingStatus() { return this.request("/api/train/status"); }
  stopTraining() { return this.request("/api/train/stop", { method: "POST" }); }
  trainingLogs(limit = 200) { return this.request(`/api/train/logs?limit=${encodeURIComponent(limit)}`); }
  validateConfig(config) { return this.request("/api/config/validate", { method: "POST", body: JSON.stringify(config), headers: { "Content-Type": "application/json" } }); }
  exportPolicy(request) { return this.request("/api/export", { method: "POST", body: JSON.stringify(request), headers: { "Content-Type": "application/json" } }); }
  exportStatus(exportId) { return this.request(`/api/export/${encodeURIComponent(exportId)}`); }
  exportDownload(exportId) { return `${this.baseUrl}/api/export/${encodeURIComponent(exportId)}/download`; }
}

