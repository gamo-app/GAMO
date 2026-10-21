import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Socio from "../components/Socio";
import Main from "../components/Main";
import Icon from "../components/Icon";
import Error from "../pages/404";
import Socioparticular from "./Socioparticular";

import { LIMITE_REGISTROS } from "../database/Config";
import {
  getProfesores,
  getRepresentantes,
  getSociosFiltrados,
} from "../database/Api";

import type { SocioData } from "../database/Api";

type Tipo = "socios" | "profesores" | "representantes" | "admins";

const rutasAgregar: Record<Tipo, { ruta: string; texto: string }> = {
  socios: { ruta: "socio", texto: "Agregar nuevo socio" },
  profesores: { ruta: "profesor", texto: "Agregar nuevo profesor" },
  representantes: {
    ruta: "representante",
    texto: "Agregar nuevo representante",
  },
  admins: { ruta: "admin", texto: "Agregar nuevo administrador" },
};

function Gestion() {
  const { id } = useParams();

  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [limite, setLimite] = useState(LIMITE_REGISTROS);

  const [respuesta, setRespuesta] = useState<SocioData[]>([]);
  const [cargando, setCargando] = useState(true);
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(false);

  // Texto escrito y texto aplicado a la búsqueda
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");

  // Filtros adicionales
  const [sede, setSede] = useState("");
  const [estado, setEstado] = useState("");
  const [tipo, setTipo] = useState<Tipo>("socios");

  // Reiniciar paginación al cambiar de categoría
  useEffect(() => {
    setPagina(1);
    setLimite(LIMITE_REGISTROS);
    setSede("");
    setEstado("");
    setBusqueda("");
    setBusquedaAplicada("");
  }, [tipo]);

  // Obtener datos
  useEffect(() => {
    let cancelado = false;

    async function cargarDatos() {
      setCargando(true);

      try {
        if (tipo === "socios") {
          const resultado = await getSociosFiltrados({
            page: pagina,
            limit: limite,
            buscar: busquedaAplicada || undefined,
          });

          if (!cancelado) {
            setRespuesta(
              Array.isArray(resultado.datos) ? resultado.datos : []
            );

            setTotalPaginas(
              resultado.paginacion?.totalPaginas ?? 1
            );
          }

          return;
        }

        let resultado: SocioData[];

        switch (tipo) {
          case "profesores":
            resultado = await getProfesores<SocioData[]>();
            break;

          case "representantes":
            resultado = await getRepresentantes<SocioData[]>();
            break;

          case "admins":
            // Agregar getAdmins cuando esté disponible en Api.tsx.
            resultado = [];
            break;

          default:
            resultado = [];
        }

        if (!cancelado) {
          setRespuesta(Array.isArray(resultado) ? resultado : []);
          setTotalPaginas(1);
        }
      } catch (error) {
        console.error("Error al cargar datos:", error);

        if (!cancelado) {
          setRespuesta([]);
          setTotalPaginas(1);
        }
      } finally {
        if (!cancelado) {
          setCargando(false);
        }
      }
    }

    cargarDatos();

    return () => {
      cancelado = true;
    };
  }, [tipo, pagina, limite, busquedaAplicada]);

  // Filtros locales adicionales.
  // La búsqueda por texto de los socios se realiza en el backend.
  const sociosFiltrados = respuesta.filter((socio) => {
    const coincideSede =
      sede === "" || String(socio.id_sede) === sede;

    const estadoSocio = String(socio.estado ?? "")
      .toLowerCase()
      .trim();

    const estadoCuota = String(socio.estado_cuota ?? "")
      .toLowerCase()
      .trim();

    const coincideEstado =
      estado === "" ||
      (estado === "morosos"
        ? estadoCuota === "vencida"
        : estadoSocio === estado);

    return coincideSede && coincideEstado;
  });

  // Mostrar más registros para profesores y representantes
  const sociosVisibles =
    tipo === "socios"
      ? sociosFiltrados
      : sociosFiltrados.slice(0, limite);

  // Vista de un socio individual
  if (id && tipo === "socios") {
    if (cargando) {
      return <Main>Cargando socio...</Main>;
    }

    const socio = respuesta.find(
      (s) => s.id_socio === Number(id)
    );

    if (!socio) {
      return <Error />;
    }

    return <Socioparticular socio={socio} />;
  }

  // Aplicar búsqueda al pulsar el botón
  const buscar = () => {
    const texto = busqueda.trim();

    setPagina(1);
    setBusqueda(texto);
    setBusquedaAplicada(texto);
  };

  return (
    <Main>
      <Header />

      <section style={{ padding: "0" }}>
        <div className="listabloques columnafija">
          <details
            className="bloque persistente estirado"
            open={filtrosAbiertos}
            onToggle={(e) =>
              setFiltrosAbiertos(e.currentTarget.open)
            }
          >
            <div
              className="divisorx2 espaciado2"
              style={{ marginBottom: "2vh" }}
            >
              <input
                type="text"
                className="blanco"
                placeholder="Buscar nombre, apellido, DNI o teléfono..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    buscar();
                  }
                }}
              />

              <button
                type="button"
                className="azul buscar"
                onClick={buscar}
                disabled={cargando}
              >
                <Icon tipo={3} tamaño={1.8} color={2} />
                Buscar
              </button>
            </div>

            <div className="divisorxy espaciado2">
              <select
                className="blanco"
                value={tipo}
                onChange={(e) =>
                  setTipo(e.target.value as Tipo)
                }
              >
                <option value="socios">Socios</option>
                <option value="profesores">Profesores</option>
                <option value="representantes">Representantes</option>
                <option value="admins">Administradores</option>
              </select>

              <select
                className="blanco"
                value={estado}
                onChange={(e) => setEstado(e.target.value)}
              >
                <option value="">Todos</option>
                <option value="morosos">Morosos</option>
                <option value="inactivo">Inactivos</option>
                <option value="activo">Activos</option>
              </select>

              <select
                className="blanco"
                value={sede}
                onChange={(e) => setSede(e.target.value)}
              >
                <option value="">Todas las sedes</option>

                {Array.from(
                  new Set(
                    respuesta
                      .map((socio) => socio.id_sede)
                      .filter((idSede) => idSede != null)
                  )
                )
                  .sort((a, b) => a - b)
                  .map((idSede) => (
                    <option key={idSede} value={idSede}>
                      Sede {idSede}
                    </option>
                  ))}
              </select>
            </div>

            <summary>
              {filtrosAbiertos ? "Cerrar filtros" : "Abrir filtros"}
            </summary>
          </details>

          <div className="bloque estirado">
            <div
              className={
                cargando || sociosVisibles.length > 0
                  ? "listay3"
                  : "listay"
              }
            >
              <Link
                to={`/agregar/${rutasAgregar[tipo].ruta}`}
                className="rectangulo"
              >
                <div className="divisorx">
                  <div
                    className="cuadrado iconoestado5"
                    style={{
                      color: "var(--siempreblanco)",
                      fontSize: "4vh",
                    }}
                  >
                    +
                  </div>

                  <div className="texto3">
                    <p>{rutasAgregar[tipo].texto}</p>
                  </div>
                </div>
              </Link>

              {cargando ? (
                <>
                  <Socio carga={true} />
                  <Socio carga={true} />
                  <Socio carga={true} />
                  <Socio carga={true} />
                  <Socio carga={true} />
                </>
              ) : sociosVisibles.length === 0 ? (
                <div className="listay">
                  <br />
                  <br />
                  <br />
                  <Icon tipo={12} tamaño={10} />
                  <p>
                    {respuesta.length === 0
                      ? "No hay registros disponibles."
                      : "No se encontraron registros con esos filtros."}
                  </p>
                </div>
              ) : (
                sociosVisibles.map((socio) => (
                  <Socio
                    key={socio.id_socio}
                    socio={socio}
                    carga={false}
                  />
                ))
              )}
            </div>
          </div>

          {tipo === "socios" && totalPaginas > 1 && (
            <div className="divisorx espaciado2">
              <button
                type="button"
                className="azul"
                disabled={pagina <= 1 || cargando}
                onClick={() =>
                  setPagina((actual) => actual - 1)
                }
              >
                Anterior
              </button>

              <span>
                Página {pagina} de {totalPaginas}
              </span>

              <button
                type="button"
                className="azul"
                disabled={
                  pagina >= totalPaginas || cargando
                }
                onClick={() =>
                  setPagina((actual) => actual + 1)
                }
              >
                Siguiente
              </button>
            </div>
          )}

          {tipo !== "socios" &&
            limite < sociosFiltrados.length && (
              <button
                type="button"
                className="azul"
                onClick={() =>
                  setLimite(
                    (anterior) =>
                      anterior + LIMITE_REGISTROS
                  )
                }
              >
                Mostrar más
              </button>
            )}
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Gestion;