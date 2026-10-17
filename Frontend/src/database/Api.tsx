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

export interface PaginacionInfo {
  paginaActual: number;
  elementosPorPagina: number;
  totalPaginas: number;
  totalSocios: number;
}

export interface ListadoSociosResponse {
  datos: SocioData[];
  paginacion: PaginacionInfo;
}

// Consulta paginada y con filtro a GET /socio/filtro
export async function getSociosFiltrados(
  page = 1,
  limit = 20,
  buscar = ""
): Promise<ListadoSociosResponse> {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });

  if (buscar.trim()) {
    params.append("buscar", buscar.trim());
  }

  return get<ListadoSociosResponse>(`/socio/filtro?${params.toString()}`);
}

// Mantiene compatibilidad si otro componente llama a getSocios()
export async function getSocios(): Promise<SocioData[]> {
  const respuesta = await getSociosFiltrados(1, 100, "");
  return respuesta.datos;
}

// Cambiar estado del socio (activo | inactivo | suspendido)
export async function cambiarEstadoSocio(
  idPersona: number,
  estado: "activo" | "inactivo" | "suspendido"
) {
  storage.invalidar("listaSocios");
  return api(`/socio/persona/${idPersona}/estado/${estado}`, {
    method: "PATCH",
  });
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