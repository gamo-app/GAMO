
import { storage } from "./Storage";

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

// Obtener socios.
export async function getSocios<T>() {
  return storage.obtenerDatos<T>(
    "listaSocios",
    () => get<T>("/socio")
  );
}

// Usuario autenticado.
export type UsuarioSesion = {
  id: string;
  id_persona?: number;
  id_sede?: number;
  id_grupo?: number;
  email: string;
  nombre_usuario?: string;
  estado?: string;
  rol?: string;
  nivel?: number;
  permisos?: Record<string, unknown>;
  persona?: {
    id_persona?: number;
    dni?: string;
    nombre?: string;
    apellido?: string;
    telefono?: string;
    fecha_nacimiento?: string;
  };
  sede?: {
    id_sede?: number;
    nombre?: string;
  };
};

export type LoginResponse = {
  mensaje: string;
  usuario: UsuarioSesion;
};

export type SesionResponse = {
  autenticado: boolean;
  usuario: UsuarioSesion;
};

// Iniciar sesión.
export async function iniciarSesion(
  email: string,
  password: string
): Promise<LoginResponse> {
  return api<LoginResponse>("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// Verificar la sesión actual.
export async function obtenerSesion(): Promise<SesionResponse> {
  return api<SesionResponse>("/login/auth/me", {
    method: "GET",
  });
}

// Cerrar sesión.
export async function cerrarSesion(): Promise<void> {
  await api<{ mensaje: string }>("/login/logout", {
    method: "POST",
  });
}

// Datos para crear un socio.
type SocioData = {
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

export async function setSocio<T>(
  socio: SocioData
): Promise<T> {
  return api<T>("/socio", {
    method: "POST",
    body: JSON.stringify(socio),
  });
}
