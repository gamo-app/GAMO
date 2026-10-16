
import { storage } from "./Storage";

// const API_URL = import.meta.env.VITE_API_URL;

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

// Autenticación.
type UsuarioSesion = {
  id: string;
  email: string;
};

type LoginResponse = {
  mensaje: string;
  usuario: UsuarioSesion;
};

type SesionResponse = {
  autenticado: boolean;
  usuario: UsuarioSesion;
};

export async function iniciarSesion(
  email: string,
  password: string
): Promise<LoginResponse> {
  return api<LoginResponse>("/login/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function obtenerSesion(): Promise<SesionResponse> {
  return api<SesionResponse>("/login/me", {
    method: "GET",
  });
}

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




