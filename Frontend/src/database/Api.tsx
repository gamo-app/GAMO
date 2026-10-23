import { storage } from "./Storage";

export const API_URL =
  import.meta.env.VITE_API_URL;

// ==========================================
// CLIENTE HTTP
// ==========================================

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

  // Permite endpoints que respondan sin cuerpo.
  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json() as Promise<T>;
  }

  return (await response.text()) as T;
}

export function get<T>(endpoint: string): Promise<T> {
  return api<T>(endpoint, { method: "GET" });
}

export function post<T, B = unknown>(
  endpoint: string,
  body: B
): Promise<T> {
  return api<T>(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function patch<T, B = unknown>(
  endpoint: string,
  body?: B
): Promise<T> {
  return api<T>(endpoint, {
    method: "PATCH",
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
}

function queryString<T extends object>(params: T) {
  const valores = Object.entries(params).filter(
    ([, valor]) => valor !== undefined && valor !== null
  );

  return valores.length
    ? `?${new URLSearchParams(
        valores.map(([clave, valor]) => [clave, String(valor)])
      )}`
    : "";
}

// ==========================================
// TIPOS
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
  estado_cuota?:
    | "pagada"
    | "pendiente"
    | "vencida"
    | "sin_cuota"
    | string
    | null;
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

export interface PersonaCreate {
  nombre: string;
  apellido: string;
  dni: string;
  telefono: string;
  fecha_nacimiento: string;
}

export interface UsuarioDatos {
  email: string;
  nombre_usuario: string;
  password: string;
}

export interface NuevoSocioPayload {
  persona: PersonaCreate;
  usuario: UsuarioDatos;
  id_plan: number;
}

export interface Credenciales {
  email: string;
  password: string;
}

export interface LoginResponse {
  jwt: string;
  [key: string]: unknown;
}

export type EstadoSocio = "activo" | "inactivo" | "suspendido";
export type Rol = "socio" | "profesor" | "representante" | "admin";

export interface BuscarRepresentantesParams {
  nombre?: string;
  apellido?: string;
  dni?: string;
  id_persona?: number;
  id_deporte?: number;
  deporte?: string;
  id_sede?: number;
  sede?: string;
}

export interface NuevoUsuarioAdminPayload {
  nombre: string;
  apellido: string;
  dni: string;
  telefono?: string | null;
  fecha_nacimiento?: string | null;
  email: string;
  password: string;
  rol: Rol;
  id_sede: number;
  id_plan?: number | null;
  id_deporte?: number | null;
}

export interface NuevoUsuarioRecepcionPayload {
  nombre: string;
  apellido: string;
  dni: string;
  telefono?: string | null;
  fecha_nacimiento?: string | null;
  email: string;
  password: string;
  rol: "socio" | "profesor";
  id_sede: number;
  id_plan?: number | null;
}

// ==========================================
// ASISTENCIA
// ==========================================

export async function getAsistencias<T = unknown>(): Promise<T> {
  return get<T>("/asistencia");
}

export async function getHistorialAsistencia<T = unknown>(
  idSocio: number,
  filtros?: { desde?: string; hasta?: string }
): Promise<T> {
  const qs = queryString({
    desde: filtros?.desde,
    hasta: filtros?.hasta,
  });
  return get<T>(
    `/asistencia/socio/${encodeURIComponent(idSocio)}${qs}`
  );
}

// ==========================================
// CLASES, CUOTAS, DEPORTES, ROLES, PERSONAS Y SEDES
// ==========================================

export async function getClases<T = unknown>(): Promise<T> {
  return get<T>("/clase");
}

export async function getCuotas<T = unknown>(): Promise<T> {
  return get<T>("/cuota");
}

export async function getDeportes<T = unknown>(): Promise<T> {
  return get<T>("/deporte");
}

export async function getGruposRoles<T = unknown>(): Promise<T> {
  return get<T>("/grupos_roles");
}

export async function getPersonas<T = unknown>(): Promise<T> {
  return get<T>("/persona");
}

export async function getSedes<T = unknown>(): Promise<T> {
  return get<T>("/sede");
}

// ==========================================
// SOCIOS, PROFESORES Y REPRESENTANTES
// ==========================================

export async function getSocios(): Promise<SocioData[]> {
  return storage.obtenerDatos<SocioData[]>(
    "listaSocios",
    () => get<SocioData[]>("/socio")
  );
}
export async function getAdmins(): Promise<SocioData[]> {
  return storage.obtenerDatos<SocioData[]>(
    "listaSocios",
    () => get<SocioData[]>("/socio")
  );
}
export async function getProfesores<T = unknown>(): Promise<T> {
  return get<T>("/profesor");
}

export async function getRepresentantes<T = unknown>(): Promise<T> {
  return get<T>("/representante");
}

export async function buscarRepresentantes<T = unknown>(
  filtros: BuscarRepresentantesParams = {}
): Promise<T> {
  return get<T>(`/representante/buscar${queryString(filtros)}`);
}

export async function getSociosFiltrados(
  params: {
    page?: number;
    limit?: number;
    buscar?: string;
  } = {}
): Promise<ListadoSociosResponse> {
  return get<ListadoSociosResponse>(
    `/socio/filtro${queryString({
      page: params.page ?? 1,
      limit: params.limit ?? 20,
      buscar: params.buscar,
    })}`
  );
}

export async function getSociosPorRolYEstado<T = unknown>(
  rol: string,
  estado: string
): Promise<T> {
  return get<T>(
    `/socio/rol/${encodeURIComponent(rol)}/estado/${encodeURIComponent(estado)}`
  );
}

export async function getSocioPorNombreYApellido<T = unknown>(
  nombre: string,
  apellido: string
): Promise<T> {
  return get<T>(
    `/socio/nombre-y-apellido/${encodeURIComponent(nombre)}/${encodeURIComponent(apellido)}`
  );
}

export async function getEstadoPago<T = unknown>(
  idUsuario: number
): Promise<T> {
  // Se conserva "ususario" porque así está publicado en la ruta de la API.
  return get<T>(`/socio/estado-pago/${encodeURIComponent(idUsuario)}`);
}

export async function cambiarEstadoPago<T = unknown>(
  idUsuario: number,
  estado: string,
  rol: string
): Promise<T> {
  return patch<T>(
    `/socio/estado-pago/${encodeURIComponent(idUsuario)}/${encodeURIComponent(estado)}${queryString({ rol })}`
  );
}

export async function cambiarEstadoSocio<T = unknown>(
  idPersona: number,
  estado: EstadoSocio
): Promise<T> {
  storage.invalidar("listaSocios");
  return patch<T>(
    `/socio/persona/${encodeURIComponent(idPersona)}/estado/${encodeURIComponent(estado)}`
  );
}

// La documentación también declara POST para esta misma ruta.
export async function cambiarEstadoSocioPost<T = unknown>(
  idPersona: number,
  estado: EstadoSocio
): Promise<T> {
  storage.invalidar("listaSocios");
  return post<T>(
    `/socio/persona/${encodeURIComponent(idPersona)}/estado/${encodeURIComponent(estado)}`,
    {}
  );
}

// ==========================================
// USUARIOS Y AUTENTICACIÓN
// ==========================================

export async function iniciarSesion(
  credenciales: Credenciales
): Promise<LoginResponse> {
  const respuesta = await post<LoginResponse, Credenciales>(
    "/usuario/login",
    credenciales
  );

  if (!respuesta.jwt) {
    throw new Error("La respuesta del login no contiene el campo jwt.");
  }

  localStorage.setItem("jwt", respuesta.jwt);
  return respuesta;
}

export function cerrarSesion(): void {
  localStorage.removeItem("jwt");
}

export async function getUsuarios<T = unknown>(): Promise<T> {
  return get<T>("/usuario");
}

export async function getMiSesion<T = unknown>(
  idUsuario: string
): Promise<T> {
  return get<T>(`/usuario/me/${encodeURIComponent(idUsuario)}`);
}

export async function crearUsuario<T = unknown>(
  usuario: UsuarioDatos
): Promise<T> {
  return post<T, UsuarioDatos>("/usuario", usuario);
}

export interface CrearSocioPayload {
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
}

export async function setSocio(
  datos: CrearSocioPayload
) {
  return api("/usuario/socio", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

// La documentación de /usuario/admin recibe un objeto plano,
// no el formato anidado de /usuario/socio.
export async function setAdmin<T = unknown>(
  usuario: NuevoUsuarioAdminPayload
): Promise<T> {
  const respuesta = await post<T, NuevoUsuarioAdminPayload>(
    "/usuario/admin",
    usuario
  );
  storage.invalidar("listaSocios");
  return respuesta;
}

// La API indica que recepción puede crear socios o profesores.
export async function setUsuarioRecepcion<T = unknown>(
  usuario: NuevoUsuarioRecepcionPayload
): Promise<T> {
  const respuesta = await post<T, NuevoUsuarioRecepcionPayload>(
    "/usuario/recepcion",
    usuario
  );
  storage.invalidar("listaSocios");
  return respuesta;
}

// Estos alias mantienen compatibilidad con nombres usados en el frontend.
// IMPORTANTE: /usuario/socio crea el alta anidada de socio; no hay rutas
// específicas /usuario/profesor o /usuario/representante en el OpenAPI aportado.
