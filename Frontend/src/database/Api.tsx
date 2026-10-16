
import { storage } from "./Storage";

const API_URL = import.meta.env.VITE_API_URL;

export async function api<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
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

export async function getSocios<T>() {
  return storage.obtenerDatos<T>(
    "listaSocios",
    () => get<T>("/socio")
  );
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

  // Guardar el JWT en el navegador
  localStorage.setItem("jwt", respuesta.jwt);

  return respuesta;
}

export function cerrarSesion(): void {
  localStorage.removeItem("jwt");
}

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
