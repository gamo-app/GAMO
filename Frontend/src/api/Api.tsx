import { storage } from "../storage/Storage";
import { carga } from "../utils/carga";
import { alerta } from "../utils/alerta";
import type { 
  PlanSocio, 
  SocioListado,
  ClaseAsistencia,
  SedeAsistencia,
  AsistenciaListado,
  SesionResponse,
  LoginResponse,
  CrearSocioResponse,
  CrearSocioRequest
} from "./Socios";



type ApiOptions = RequestInit & {
  mostrarCarga?: boolean;
  mostrarError?: boolean;
};

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? "" : "https://gamo.gamo-app-com.workers.dev")
).replace(/\/+$/, "");

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
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
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

export async function registrarAsistencia(datos: {
  uuid_clase: string;
  fecha: string;
  codigo_credencial: string;
}): Promise<void> {
  await post("/asistencia", datos, { mostrarCarga: true });
  alerta("¡Asistencia registrada correctamente!", "exito");
}

export async function registrarAsistenciaQr(
  qr_payload: string
): Promise<void> {
  await post("/asistencia/qr/escaneo", { qr_payload }, {
    mostrarCarga: true,
  });
  alerta("¡Asistencia registrada correctamente!", "exito");
}

export function obtenerMisAsistencias(): Promise<AsistenciaListado[]> {
  return get<AsistenciaListado[]>("/asistencia/mis-asistencias");
}

export function obtenerQrSede(
  idSede: number
): Promise<{ qr_payload: string }> {
  return get<{ qr_payload: string }>(`/asistencia/qr/sede/${idSede}`);
}

export function obtenerClasesAsistencia(): Promise<ClaseAsistencia[]> {
  return get<ClaseAsistencia[]>("/clase");
}

export function obtenerSedesAsistencia(): Promise<SedeAsistencia[]> {
  return get<SedeAsistencia[]>("/sede");
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
