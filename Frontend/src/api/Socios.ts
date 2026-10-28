export type SocioUsuario = {
  uuid_usuario: string;
  DNI: number;
  nombre: string;
  apellido: string;
  fecha_nacimiento: string;
};

export type PlanSocio = {
  id_plan: number;
  nombre: string;
  precio_semanal: number;
  clases_semanales: number;
};

export type MembresiaSocio = {
  id_membresia: number;
  id_plan: number;
  fecha_inicio: string;
  fecha_fin: string;
  porcentaje_descuento: number;
  plan: PlanSocio | null;
};

export type SocioListado = {
  codigo_credencial: string;
  uuid_usuario: string;
  usuario: SocioUsuario | null;
  membresias: MembresiaSocio[];
};

export type EstadoSocio =
  | "activo"
  | "pendiente"
  | "inactivo"
  | "sin_membresia";



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

export function evaluarMembresia(
  membresias: MembresiaSocio[],
  hoy = fechaLocalActual()
): { estado: EstadoSocio; membresia: MembresiaSocio | null } {
  if (membresias.length === 0) {
    return { estado: "sin_membresia", membresia: null };
  }

  const activas = membresias
    .filter(
      ({ fecha_inicio, fecha_fin }) =>
        fecha_inicio <= hoy && fecha_fin >= hoy
    )
    .sort((a, b) => b.fecha_inicio.localeCompare(a.fecha_inicio));

  if (activas.length > 0) {
    return { estado: "activo", membresia: activas[0] };
  }

  const futuras = membresias
    .filter(({ fecha_inicio }) => fecha_inicio > hoy)
    .sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio));

  if (futuras.length > 0) {
    return { estado: "pendiente", membresia: futuras[0] };
  }

  const anteriores = [...membresias].sort((a, b) =>
    b.fecha_fin.localeCompare(a.fecha_fin)
  );

  return { estado: "inactivo", membresia: anteriores[0] };
}

function fechaLocalActual(): string {
  const hoy = new Date();
  const año = hoy.getFullYear();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");

  return `${año}-${mes}-${dia}`;
}
