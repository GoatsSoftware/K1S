export type ApiResult = {
  success: boolean;
  error?: string;
  [key: string]: any;
};

export async function api(path: string, body?: unknown): Promise<ApiResult> {
  try {
    const res = await fetch(`/api/${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch {
      return { success: false, error: text || `HTTP ${res.status}` };
    }
  } catch {
    return { success: false, error: "Serveur injoignable" };
  }
}

export const getPlayer = () => localStorage.getItem("goat-player") || "Player";
export const setPlayer = (name: string) => localStorage.setItem("goat-player", name);
