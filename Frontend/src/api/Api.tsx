import { storage } from "../storage/Storage";
import type { 
  PlanSocio, 
  SocioListado,
  SesionResponse,
  LoginResponse,
  CrearSocioResponse,
  CrearSocioRequest
} from "./Socios";

export async function api<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(endpoint, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    let message = errorText;

    try {
      const parsed: { detail?: string; mensaje?: string } =
        JSON.parse(errorText);
      message = parsed.detail || parsed.mensaje || errorText;
    } catch {
      // The response body is not JSON.
    }

    console.error("Error del backend:", {
      endpoint,
      status: response.status,
      error: errorText,
    });
    throw new Error(message || `Error ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function get<T>(endpoint: string): Promise<T> {
  return api<T>(endpoint, { method: "GET" });
}

export async function iniciarSesion(
  email: string,
  password: string
): Promise<LoginResponse> {
  return api<LoginResponse>("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function obtenerSesion(): Promise<SesionResponse> {
  return get<SesionResponse>("/login/auth/me");
}

export async function cerrarSesion(): Promise<void> {
  await api<{ mensaje: string }>("/login/logout", {
    method: "POST",
  });
}

export async function getSocios(): Promise<SocioListado[]> {
  return storage.obtenerDatos<SocioListado[]>(
    "listaSocios-v2",
    () => get<SocioListado[]>("/socio")
  );
}

export async function getPlanes(): Promise<PlanSocio[]> {
  return get<PlanSocio[]>("/socio/planes");
}



export async function setSocio(
  socio: CrearSocioRequest
): Promise<CrearSocioResponse> {
  const respuesta = await api<CrearSocioResponse>("/socio", {
    method: "POST",
    body: JSON.stringify(socio),
  });

  storage.invalidar("listaSocios-v2");
  return respuesta;
}
