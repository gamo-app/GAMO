import { storage } from "./Storage";

export const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8787";

  export async function api<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = localStorage.getItem("jwt");

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();

    console.error("Error del backend:", {
      endpoint,
      status: response.status,
      error,
    });

    throw new Error(`Error ${response.status}: ${error}`);
  }

  return response.json();
}

export async function get<T>(endpoint: string): Promise<T> {
  return api<T>(endpoint, { method: "GET" });
}

// ==========================================
// TIPOS ALINEADOS CON base_socio.py
// ==========================================

export interface SocioData {
  id_socio: number;
  id_persona?: number | null;
  id_sede?: number | null;
  codigo_credencial?: string | null;
  sede?: string | null;
  nombre?: string | null;
  apellido?: string | null;
  dni?: string | null;
  telefono?: string | null;
  email?: string | null;
  estado?: "activo" | "inactivo" | "suspendido" | string | null;
  plan?: string | null;
  fecha_alta?: string | null;
  fecha_vencimiento?: string | null;
  estado_cuota?: "pagada" | "pendiente" | "vencida" | "sin_cuota" | string | null;
  monto_cuota?: number | null;
}
export async function getProfesores<T>() {
  return storage.obtenerDatos<T>(
    "listaSocios",
    () => get<T>("/socio")
  );
}
export async function getAdmins<T>() {
  return storage.obtenerDatos<T>(
    "listaSocios",
    () => get<T>("/socio")
  );
}

export async function getRepresentantes<T>() {
  return storage.obtenerDatos<T>(
    "listaSocios",
    () => get<T>("/socio")
  );
}

// ==========================================
// AUTENTICACIÓN Y ALTA DE SOCIO
// ==========================================

type Credenciales = {
  email: string;
  password: string;
};

type LoginResponse = {
  jwt: string;
};

export async function iniciarSesion(
  credenciales: Credenciales
): Promise<LoginResponse> {
  const respuesta = await api<LoginResponse>("/usuario/login", {
    method: "POST",
    body: JSON.stringify(credenciales),
  });

  localStorage.setItem("jwt", respuesta.jwt);
  return respuesta;
}

export function cerrarSesion(): void {
  localStorage.removeItem("jwt");
}

type NuevoSocioPayload = {
  persona: {
    nombre: string;
    apellido: string;
    dni: string;
    telefono: string;
    fecha_nacimiento: string;
  };
  usuario: {
    email: string;
    nombre_usuario: string;
    password: string;
  };
  id_plan: number;
};

export async function setSocio<T>(socio: NuevoSocioPayload): Promise<T> {
  storage.invalidar("listaSocios");
  return api<T>("/usuario/socio", { 
    method: "POST",
    body: JSON.stringify(socio),
  });
}
