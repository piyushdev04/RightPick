const BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

async function handleResponse(res) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function fetchProducts({ skip = 0, limit = 50 } = {}) {
  const res = await fetch(`${BASE_URL}/products?skip=${skip}&limit=${limit}`);
  return handleResponse(res);
}

export async function fetchProduct(id) {
  const res = await fetch(`${BASE_URL}/products/${id}`);
  return handleResponse(res);
}

export async function chatQuery(message, topK = 8) {
  const res = await fetch(`${BASE_URL}/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, top_k: topK }),
  });
  return handleResponse(res);
}


