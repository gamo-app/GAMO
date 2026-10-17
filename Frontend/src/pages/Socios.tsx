/*import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Socio from "../components/Socio";
import Main from "../components/Main";
import Socioparticular from "./Socioparticular";
import Icon from "../components/Icon";
import {
  getSociosFiltrados,
  cambiarEstadoSocio,
} from "../database/Api";
import type { SocioData, PaginacionInfo } from "../database/Api";

function Socios() {
  const { id } = useParams();

  const [respuesta, setRespuesta] = useState<SocioData[]>([]);
  const [paginacion, setPaginacion] = useState<PaginacionInfo>({
    paginaActual: 1,
    elementosPorPagina: 20,
    totalPaginas: 1,
    totalSocios: 0,
  });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [busqueda, setBusqueda] = useState("");
  const [busquedaDebounced, setBusquedaDebounced] = useState("");
  const [planFiltro, setPlanFiltro] = useState("");
  const [estado, setEstado] = useState("");

  const cargarSocios = useCallback(
    async (pagina = 1, termino = "") => {
      setCargando(true);
      setError(null);

      try {
        const resultado = await getSociosFiltrados(pagina, 20, termino);
        setRespuesta(resultado.datos || []);
        if (resultado.paginacion) {
          setPaginacion(resultado.paginacion);
        }
      } catch (err) {
        console.error("Error al cargar socios:", err);
        setError(
          "No se pudieron cargar los socios. Verificá que el backend esté corriendo."
        );
      } finally {
        setCargando(false);
      }
    },
    []
  );

  // Debounce de 400ms para el texto buscado
  useEffect(() => {
    const timer = setTimeout(() => {
      setBusquedaDebounced(busqueda);
      setPaginacion((prev) =>
        prev.paginaActual === 1 ? prev : { ...prev, paginaActual: 1 }
      );
    }, 400);

    return () => clearTimeout(timer);
  }, [busqueda]);

  // Único efecto encargado de disparar la consulta al backend
  useEffect(() => {
    cargarSocios(paginacion.paginaActual, busquedaDebounced);
  }, [paginacion.paginaActual, busquedaDebounced, cargarSocios]);

  const handleCambiarEstadoSocio = async (socio: SocioData) => {
    if (!socio.id_persona) {
      alert(
        "Falta id_persona en la respuesta del backend. Asegurate de agregarlo en base_socio.py."
      );
      return;
    }

    const nuevoEstado =
      socio.estado === "inactivo" ? "activo" : "inactivo";

    try {
      await cambiarEstadoSocio(socio.id_persona, nuevoEstado);
      await cargarSocios(paginacion.paginaActual, busquedaDebounced);
    } catch (err) {
      console.error("Error al actualizar estado del socio:", err);
      alert("No se pudo actualizar el estado del socio.");
    }
  };

  // Filtros locales complementarios (Plan y Estado / Morosos)
  const sociosFiltrados = respuesta.filter((socio) => {
    const coincidePlan =
      planFiltro === "" || (socio.plan ?? "") === planFiltro;

    const estadoSocio = (socio.estado ?? "").toLowerCase().trim();
    const estadoCuota = (socio.estado_cuota ?? "").toLowerCase().trim();

    const coincideEstado =
      estado === "" ||
      (estado === "morosos"
        ? estadoCuota === "vencida"
        : estadoSocio === estado);

    return coincidePlan && coincideEstado;
  });

  // Vista de detalle de un socio particular (/socios/:id)
  if (id) {
    if (cargando) {
      return <Main>Cargando socio...</Main>;
    }

    const socio = respuesta.find((s) => s.id_socio === Number(id));

    if (!socio) {
      return <Main>Socio no encontrado</Main>;
    }

    return (
      <Socioparticular
        socio={socio}
        onCambiarEstado={handleCambiarEstadoSocio}
      />
    );
  }

  const planesDisponibles = Array.from(
    new Set(
      respuesta
        .map((s) => s.plan)
        .filter((p): p is string => Boolean(p))
    )
  );

  return (
    <Main>
      <Header />

      <section style={{ padding: "0" }}>
        <div className="listabloques columnafija">
          <div className="bloque persistente estirado">
            <div className="divisorx espaciado2">
              <input
                type="text"
                className="blanco"
                placeholder="Buscar por nombre, apellido o DNI..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
              />
              <button
                type="button"
                className="botoniconoazul"
                onClick={() => cargarSocios(1, busqueda)}
              >
                <Icon tipo={3} color={2} />
                Buscar
              </button>
            </div>

            <div className="divisorx espaciado2">
              <select
                className="blanco"
                value={planFiltro}
                onChange={(e) => setPlanFiltro(e.target.value)}
              >
                <option value="">Todos los planes</option>
                {planesDisponibles.map((plan) => (
                  <option key={plan} value={plan}>
                    {plan}
                  </option>
                ))}
              </select>

              <Link to="/agregarsocio" className="azul pc">
                Agregar nuevo socio
              </Link>
            </div>

            <div className="listax overflow">
              <div className="contenidolista">
                {[
                  { texto: "Todos", valor: "" },
                  { texto: "Morosos", valor: "morosos" },
                  { texto: "Inactivos", valor: "inactivo" },
                  { texto: "Activos", valor: "activo" },
                ].map((filtro) => (
                  <button
                    key={filtro.texto}
                    type="button"
                    className={`${
                      estado === filtro.valor ? "azul" : "blanco"
                    } miniboton`}
                    onClick={() => setEstado(filtro.valor)}
                  >
                    {filtro.texto}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="bloque estirado">
            {error && (
              <div className="listay">
                <p style={{ color: "var(--rojo)", fontWeight: "bold" }}>
                  {error}
                </p>
              </div>
            )}

            {cargando ? (
              <>
                <Socio carga={true} />
                <Socio carga={true} />
                <Socio carga={true} />
                <Socio carga={true} />
                <Socio carga={true} />
              </>
            ) : respuesta.length === 0 ? (
              <div className="listay">
                <p>No hay socios registrados.</p>
              </div>
            ) : sociosFiltrados.length === 0 ? (
              <div className="listay">
                <p>No se encontraron socios con esos filtros.</p>
              </div>
            ) : (
              sociosFiltrados.map((socio) => (
                <Socio
                  key={socio.id_socio}
                  socio={socio}
                  sede={socio.sede ?? undefined}
                  carga={false}
                  onCambiarEstado={handleCambiarEstadoSocio}
                />
              ))
            )}

        
            {!cargando && paginacion.totalSocios > 0 && (
              <div className="bloque4" style={{ marginTop: "1vh" }}>
                <p>
                  Página {paginacion.paginaActual} de{" "}
                  {paginacion.totalPaginas || 1} ({paginacion.totalSocios}{" "}
                  socios)
                </p>
                <div className="divisorx">
                  <button
                    type="button"
                    className="blanco miniboton"
                    disabled={paginacion.paginaActual <= 1}
                    onClick={() =>
                      setPaginacion((prev) => ({
                        ...prev,
                        paginaActual: prev.paginaActual - 1,
                      }))
                    }
                  >
                    Anterior
                  </button>
                  <button
                    type="button"
                    className="azul miniboton"
                    disabled={
                      paginacion.paginaActual >= paginacion.totalPaginas
                    }
                    onClick={() =>
                      setPaginacion((prev) => ({
                        ...prev,
                        paginaActual: prev.paginaActual + 1,
                      }))
                    }
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}

            <br />

            <Link to="/agregarsocio" className="azul mobile">
              Agregar nuevo socio
            </Link>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Socios;
*/