import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";

import Header from "../components/Header";
import Icon from "../components/Icon";
import Main from "../components/Main";
import NavBar from "../components/Navbar";
import Socio from "../components/Socio";
import { get, getSocios } from "../database/Api";
import {
  evaluarMembresia,
  type EstadoSocio,
  type SocioListado,
} from "../database/Socios";

type Tipo = "socios" | "profesores" | "representantes" | "admins";

type UsuarioGestion = {
  uuid_usuario: string;
  DNI: number;
  nombre: string;
  apellido: string;
  id_rol: number;
};

type RolGestion = {
  id_rol: number;
  nombre: string;
};

type ProfesorGestion = {
  id_profesor: number;
  uuid_usuario: string;
};

type RepresentanteGestion = {
  id_representante: number;
  id_profesor: number;
  id_deporte: number;
};

type RegistroGestion = {
  id: string;
  nombre: string;
  apellido: string;
  dni: string;
  subtitulo: string;
  socio?: SocioListado;
};

const categorias: Record<Tipo, string> = {
  socios: "socio",
  profesores: "profesor",
  representantes: "representante",
  admins: "administrador",
};

function normalizar(texto: string): string {
  return texto.trim().toLocaleLowerCase();
}

async function cargarRegistros(tipo: Tipo): Promise<RegistroGestion[]> {
  if (tipo === "socios") {
    const socios = await getSocios();
    return socios.map((socio) => ({
      id: socio.codigo_credencial,
      nombre: socio.usuario?.nombre ?? "Usuario no disponible",
      apellido: socio.usuario?.apellido ?? "",
      dni: socio.usuario ? String(socio.usuario.DNI) : "",
      subtitulo: "Socio",
      socio,
    }));
  }

  const usuarios = await get<UsuarioGestion[]>("/usuario");
  const usuariosPorId = new Map(
    usuarios.map((usuario) => [usuario.uuid_usuario, usuario])
  );

  if (tipo === "profesores") {
    const profesores = await get<ProfesorGestion[]>("/profesor");
    return profesores.map((profesor) => {
      const usuario = usuariosPorId.get(profesor.uuid_usuario);
      return {
        id: String(profesor.id_profesor),
        nombre: usuario?.nombre ?? "Usuario no disponible",
        apellido: usuario?.apellido ?? "",
        dni: usuario ? String(usuario.DNI) : "",
        subtitulo: "Profesor",
      };
    });
  }

  if (tipo === "representantes") {
    const [representantes, profesores] = await Promise.all([
      get<RepresentanteGestion[]>("/representante"),
      get<ProfesorGestion[]>("/profesor"),
    ]);
    const profesoresPorId = new Map(
      profesores.map((profesor) => [profesor.id_profesor, profesor])
    );

    return representantes.map((representante) => {
      const profesor = profesoresPorId.get(representante.id_profesor);
      const usuario = profesor
        ? usuariosPorId.get(profesor.uuid_usuario)
        : undefined;

      return {
        id: String(representante.id_representante),
        nombre: usuario?.nombre ?? "Usuario no disponible",
        apellido: usuario?.apellido ?? "",
        dni: usuario ? String(usuario.DNI) : "",
        subtitulo: `Representante · Deporte ${representante.id_deporte}`,
      };
    });
  }

  const roles = await get<RolGestion[]>("/rol");
  const rolesPorId = new Map(roles.map((rol) => [rol.id_rol, rol.nombre]));

  return usuarios
    .filter((usuario) =>
      normalizar(rolesPorId.get(usuario.id_rol) ?? "").includes("admin")
    )
    .map((usuario) => ({
      id: usuario.uuid_usuario,
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      dni: String(usuario.DNI),
      subtitulo: rolesPorId.get(usuario.id_rol) ?? "Administrador",
    }));
}

function Gestion() {
  const { id } = useParams();
  const [tipo, setTipo] = useState<Tipo>("socios");
  const [registros, setRegistros] = useState<RegistroGestion[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [estado, setEstado] = useState<EstadoSocio | "">("");
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(true);

  useEffect(() => {
    let activo = true;

    cargarRegistros(tipo)
      .then((resultado) => {
        if (activo) {
          setRegistros(resultado);
        }
      })
      .catch((error: unknown) => {
        console.error(`Error al cargar ${tipo}:`, error);
        if (activo) {
          setRegistros([]);
          setError(
            error instanceof Error
              ? error.message
              : `No se pudieron cargar los registros de ${tipo}.`
          );
        }
      })
      .finally(() => {
        if (activo) {
          setCargando(false);
        }
      });

    return () => {
      activo = false;
    };
  }, [tipo]);

  const registrosFiltrados = useMemo(() => {
    const texto = normalizar(busquedaAplicada);

    return registros.filter((registro) => {
      const coincideBusqueda =
        texto === "" ||
        `${registro.nombre} ${registro.apellido}`
          .toLocaleLowerCase()
          .includes(texto) ||
        registro.dni.includes(texto);
      const estadoRegistro = registro.socio
        ? evaluarMembresia(registro.socio.membresias).estado
        : "";

      return (
        coincideBusqueda && (estado === "" || estadoRegistro === estado)
      );
    });
  }, [registros, busquedaAplicada, estado]);

  if (id) {
    return <Navigate to="/gestion" replace />;
  }

  function buscar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusquedaAplicada(busqueda.trim());
  }

  function cambiarTipo(event: React.ChangeEvent<HTMLSelectElement>) {
    setTipo(event.target.value as Tipo);
    setCargando(true);
    setError("");
    setEstado("");
    setBusqueda("");
    setBusquedaAplicada("");
  }

  return (
    <Main>
      <Header />

      <section style={{ padding: 0 }}>
        <div className="listabloques columnafija">
          <details
            className="bloque persistente estirado"
            open={filtrosAbiertos}
            onToggle={(event) =>
              setFiltrosAbiertos(event.currentTarget.open)
            }
          >
            <form
              onSubmit={buscar}
              className="divisorx2 espaciado2"
              style={{ marginBottom: "2vh" }}
            >
              <input
                type="search"
                className="blanco"
                placeholder="Buscar nombre, apellido o DNI..."
                aria-label="Buscar por nombre, apellido o DNI"
                value={busqueda}
                onChange={(event) => setBusqueda(event.target.value)}
              />
              <button
                type="submit"
                className="azul buscar"
                disabled={cargando}
              >
                <Icon tipo={3} tamaño={1.8} color={2} />
                Buscar
              </button>
            </form>

            <div className="divisorxy espaciado2">
              <select
                className="blanco"
                aria-label="Tipo de usuario"
                value={tipo}
                onChange={cambiarTipo}
              >
                <option value="socios">Socios</option>
                <option value="profesores">Profesores</option>
                <option value="representantes">Representantes</option>
                <option value="admins">Administradores</option>
              </select>

              <select
                className="blanco"
                aria-label="Filtrar socios por estado de membresía"
                value={estado}
                disabled={tipo !== "socios"}
                onChange={(event) =>
                  setEstado(event.target.value as EstadoSocio | "")
                }
              >
                <option value="">Todos</option>
                <option value="activo">Activos</option>
                <option value="pendiente">Pendientes</option>
                <option value="inactivo">Inactivos</option>
                <option value="sin_membresia">Sin membresía</option>
              </select>

              <select
                className="blanco"
                aria-label="Filtro por sede no disponible"
                disabled
                value=""
                title="El esquema actual no relaciona usuarios con sedes."
              >
                <option value="">Filtro por sede no disponible</option>
              </select>
            </div>

            <summary>
              {filtrosAbiertos ? "Cerrar filtros" : "Abrir filtros"}
            </summary>
          </details>

          <div className="bloque estirado">
            <div
              className={
                cargando || registrosFiltrados.length > 0
                  ? "listay3"
                  : "listay"
              }
            >
              {tipo === "socios" ? (
                <Link to="/agregarsocio" className="rectangulo">
                  <div className="divisorx">
                    <div className="cuadrado iconoestado5" aria-hidden="true">
                      +
                    </div>
                    <div className="texto3">
                      <p>Agregar nuevo socio</p>
                    </div>
                  </div>
                </Link>
              ) : (
                <div
                  className="rectangulo"
                  aria-disabled="true"
                  title={`El alta de ${categorias[tipo]} no está implementada.`}
                >
                  <div className="divisorx">
                    <div className="cuadrado iconoestado5" aria-hidden="true">
                      +
                    </div>
                    <div className="texto3">
                      <p>Alta de {categorias[tipo]} no disponible</p>
                    </div>
                  </div>
                </div>
              )}

              {cargando ? (
                <>
                  <Socio carga />
                  <Socio carga />
                  <Socio carga />
                  <Socio carga />
                  <Socio carga />
                </>
              ) : error ? (
                <p role="alert">{error}</p>
              ) : registrosFiltrados.length === 0 ? (
                <div className="listay">
                  <Icon tipo={12} tamaño={10} />
                  <p>
                    {registros.length === 0
                      ? `No hay ${tipo} registrados.`
                      : "No se encontraron registros con esos filtros."}
                  </p>
                </div>
              ) : (
                registrosFiltrados.map((registro) =>
                  registro.socio ? (
                    <Socio
                      key={registro.id}
                      socio={registro.socio}
                    />
                  ) : (
                    <article className="rectangulo" key={registro.id}>
                      <div className="divisorx">
                        <div className="cuadrado iconoestado4 iconoperfil">
                          <Icon tipo={2} color={0} tamaño={3.6} />
                        </div>
                        <div className="texto2">
                          <h4>
                            {`${registro.nombre} ${registro.apellido}`.trim()}
                          </h4>
                          <div className="divisorx3">
                            <p>{registro.subtitulo}</p>
                            {registro.dni && (
                              <>
                                <p aria-hidden="true">·</p>
                                <p>DNI {registro.dni}</p>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </article>
                  )
                )
              )}
            </div>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Gestion;
