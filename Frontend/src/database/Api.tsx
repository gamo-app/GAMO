
import { storage } from "./Storage";
import type { PlanSocio, SocioListado } from "./Socios";

// ============================================
// Cliente HTTP
// ============================================

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
      const parsed = JSON.parse(errorText);
      message = parsed.detail || parsed.mensaje || errorText;
    } catch {
      // La respuesta no contiene JSON.
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

export async function get<T>(endpoint: string): Promise<T> {
  return api<T>(endpoint, { method: "GET" });
}

// ============================================
// Tipos de usuario y autenticación
// ============================================

export type UsuarioSesion = {
  uuid_usuario: string;
  DNI: number;
  nombre: string;
  apellido: string;
  fecha_nacimiento: string;
  rol: {
    id_rol: number;
    nombre: string;
    permisos: Record<string, boolean>;
  } | null;
  email: string | null;
};

export type LoginResponse = {
  mensaje: string;
  usuario: {
    id: string;
    email: string | null;
  };
};

export type SesionResponse = {
  usuario: UsuarioSesion;
};

// ============================================
// Iniciar sesión
// ============================================

export async function iniciarSesion(
  email: string,
  password: string
): Promise<LoginResponse> {
  return api<LoginResponse>("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// ============================================
// Recuperar sesión existente
// ============================================

export async function obtenerSesion(): Promise<SesionResponse> {
  return api<SesionResponse>("/login/auth/me", {
    method: "GET",
  });
}

// ============================================
// Cerrar sesión
// ============================================

export async function cerrarSesion(): Promise<void> {
  await api<{ mensaje: string }>("/login/logout", {
    method: "POST",
  });
}

// ============================================
// Socios
// ============================================

export async function getSocios(): Promise<SocioListado[]> {
  return storage.obtenerDatos<SocioListado[]>(
    "listaSocios-v2",
    () => get<SocioListado[]>("/socio")
  );
}

export async function getPlanes(): Promise<PlanSocio[]> {
  return get<PlanSocio[]>("/socio/planes");
}

export type CrearSocioRequest = {
  id_plan: number;
  fecha_inicio: string;
  fecha_fin: string;
  usuario: {
    nombre: string;
    apellido: string;
    fecha_nacimiento: string;
    DNI: number;
    email: string;
    password: string;
  };
};

export type CrearSocioResponse = {
  mensaje: string;
  usuario: {
    uuid_usuario: string;
    DNI: number;
    nombre: string;
    apellido: string;
    fecha_nacimiento: string;
    id_rol: number;
    email: string;
  };
  socio: {
    codigo_credencial: string;
    uuid_usuario: string;
  };
  membresia: {
    id_membresia: number;
    codigo_credencial: string;
    id_plan: number;
    fecha_inicio: string;
    fecha_fin: string;
  };
};

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
