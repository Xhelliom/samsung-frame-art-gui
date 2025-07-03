export interface ImageItem {
  file: string;
  remote_filename?: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function handleJson(res: Response) {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || "Erreur serveur");
  }
  return res.json();
}

export const api = {
  async listImages(): Promise<ImageItem[]> {
    const res = await fetch(`${API_BASE}/api/images`, { cache: "no-store" });
    return handleJson(res);
  },
  async uploadImage(file: File): Promise<ImageItem> {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: fd,
    });
    return handleJson(res);
  },
  async setImage(remote_filename: string) {
    const res = await fetch(`${API_BASE}/api/set-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ remote_filename }),
    });
    return handleJson(res);
  },
  async searchUnsplash(query: string) {
    const res = await fetch(`${API_BASE}/api/search-unsplash?query=` + encodeURIComponent(query));
    return handleJson(res);
  },
  async unsplashFeatured() {
    const res = await fetch(`${API_BASE}/api/unsplash-featured`);
    return handleJson(res);
  },
  async trackDownload(download_location: string) {
    // Unsplash demande un appel sans authentification pour tracer les downloads
    try {
      await fetch(download_location, { mode: "no-cors" });
    } catch {}
  },
  async getCurrentImage() {
    const res = await fetch(`${API_BASE}/api/current-image`);
    return handleJson(res);
  },
  async sendToTV(filename: string): Promise<ImageItem> {
    const res = await fetch(`${API_BASE}/api/send-to-tv`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    });
    return handleJson(res);
  },
  // Debug endpoints
  async debugApiVersion() {
    const res = await fetch(`${API_BASE}/api/debug/api-version`);
    return handleJson(res);
  },
  async debugTvStatus() {
    const res = await fetch(`${API_BASE}/api/debug/tv-status`);
    return handleJson(res);
  },
  async debugSetArtMode(mode: "on" | "off") {
    const res = await fetch(`${API_BASE}/api/debug/set-artmode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    });
    return handleJson(res);
  },
  async debugAvailableArt() {
    const res = await fetch(`${API_BASE}/api/debug/available-art`);
    return handleJson(res);
  },
  async debugArtModeSettings() {
    const res = await fetch(`${API_BASE}/api/debug/artmode-settings`);
    return handleJson(res);
  },
  async debugTestUpload(filename: string) {
    const res = await fetch(`${API_BASE}/api/debug/test-upload`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    });
    return handleJson(res);
  },
  async debugSlideshowStatus() {
    const res = await fetch(`${API_BASE}/api/debug/slideshow-status`);
    return handleJson(res);
  },
  async debugPowerOn() {
    const res = await fetch(`${API_BASE}/api/debug/power-on`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleJson(res);
  },
  async debugSendKey(key: string) {
    const res = await fetch(`${API_BASE}/api/debug/send-key`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key }),
    });
    return handleJson(res);
  },
  async debugDeviceInfo() {
    const res = await fetch(`${API_BASE}/api/debug/device-info`);
    return handleJson(res);
  },
  async debugAppList() {
    const res = await fetch(`${API_BASE}/api/debug/app-list`);
    return handleJson(res);
  },
  async debugRunApp(appId: string) {
    const res = await fetch(`${API_BASE}/api/debug/run-app`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ app_id: appId }),
    });
    return handleJson(res);
  },
}; 