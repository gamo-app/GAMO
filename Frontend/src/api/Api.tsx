import { storage } from "../storage/Storage";
import { carga } from "../utils/carga";
import { alerta } from "../utils/alerta";
import type { 
  PlanSocio, 
  SocioListado,
  SesionResponse,
  LoginResponse,
  CrearSocioResponse,
  CrearSocioRequest
} from "./Socios";



type ApiOptions = RequestInit & {
  mostrarCarga?: boolean;
  mostrarError?: boolean;
};

export async function api<T>(
  endpoint: string,
  options?: ApiOptions
): Promise<T> {
  const {
    mostrarCarga = false,
    mostrarError = true,
    ...requestOptions
  } = options ?? {};

  const cerrarCarga = mostrarCarga ? carga() : undefined;

  try {
    const response = await fetch(endpoint, {
      ...requestOptions,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...requestOptions.headers,
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
        // La respuesta no contiene JSON.
      }

      throw new Error(message || `Error ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    const mensaje =
      error instanceof Error
        ? error.message
        : "Ocurrió un error inesperado.";

    console.error("Error de API:", {
      endpoint,
      error: mensaje,
    });

    if (mostrarError) {
      alerta(mensaje, "error");
    }

    throw error;
  } finally {
    cerrarCarga?.();
  }
}




export function get<T>(
  endpoint: string,
  options?: ApiOptions
): Promise<T> {
  return api<T>(endpoint, {
    ...options,
    method: "GET",
  });
}
export function post<T>(
  endpoint: string,
  body?: unknown,
  options?: ApiOptions
): Promise<T> {
  return api<T>(endpoint, {
    ...options,
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export async function iniciarSesion(
  email: string,
  password: string
): Promise<LoginResponse> {
  return api<LoginResponse>("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    mostrarCarga: true,
  });
}

export async function registrarAsistencia(
  idUsuario: string
): Promise<boolean> {
  try {
    await post(
      "/asistencia",
      { uuid_usuario: idUsuario },
      {
        mostrarCarga: true,
        mostrarError: false,
      }
    );

    alerta("¡Asistencia registrada correctamente!");
    return true;
  } catch (error) {
    console.error("Error al registrar la asistencia:");

    alerta("No se pudo registrar la asistencia.");
    return false;
  }
}


export async function obtenerSesion(): Promise<SesionResponse> {
  return get<SesionResponse>("/login/auth/me", {
    mostrarError: false
  });
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
