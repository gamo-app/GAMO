import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Header from "../components/Header";
import Icon from "../components/Icon";
import Main from "../components/Main";
import NavBar from "../components/Navbar";
import Socio from "../components/Socio";
import { getSocios } from "../database/Api";
import {
  evaluarMembresia,
  type EstadoSocio,
  type SocioListado,
} from "../database/Socios";
import Socioparticular from "./Socioparticular";

function Socios() {
  const { id } = useParams();
  const [respuesta, setRespuesta] = useState<SocioListado[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [estado, setEstado] = useState<EstadoSocio | "">("");
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(true);

  useEffect(() => {
    let activo = true;

    getSocios()
      .then((resultado) => {
        if (activo) {
          setRespuesta(resultado);
        }
      })
      .catch((error: unknown) => {
        console.error("Error al cargar socios:", error);
        if (activo) {
          setError("No se pudieron cargar los socios. Intentá nuevamente.");
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
  }, []);

  const sociosFiltrados = useMemo(() => {
    const texto = busquedaAplicada.toLocaleLowerCase();

    return respuesta.filter((socio) => {
      const nombre = socio.usuario
        ? `${socio.usuario.nombre} ${socio.usuario.apellido}`.toLocaleLowerCase()
        : "";
      const dni = socio.usuario ? String(socio.usuario.DNI) : "";
      const estadoSocio = evaluarMembresia(socio.membresias).estado;
      const coincideBusqueda =
        texto.length === 0 || nombre.includes(texto) || dni.includes(texto);
      const coincideEstado = estado === "" || estadoSocio === estado;

      return coincideBusqueda && coincideEstado;
    });
  }, [respuesta, busquedaAplicada, estado]);

  if (id) {
    if (cargando) {
      return <Main>Cargando socio...</Main>;
    }

    const socio = respuesta.find(
      (item) => item.codigo_credencial === id
    );

    if (!socio) {
      return <Main>Socio no encontrado</Main>;
    }

    return <Socioparticular socio={socio} />;
  }

  function buscar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusquedaAplicada(busqueda.trim());
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
            <form onSubmit={buscar} className="divisorx2 espaciado2">
              <input
                type="search"
                className="blanco"
                placeholder="Buscar nombre, apellido o DNI..."
                value={busqueda}
                onChange={(event) => setBusqueda(event.target.value)}
              />
              <button
                type="submit"
                className="azul buscar"
                aria-label="Buscar socios"
                disabled={cargando}
              >
                <Icon tipo={3} tamaño={1.8} color={2} />
              </button>
            </form>

            <div className="divisorxy espaciado2">
              <select
                className="blanco"
                aria-label="Filtrar socios por estado de membresía"
                value={estado}
                onChange={(event) =>
                  setEstado(event.target.value as EstadoSocio | "")
                }
              >
                <option value="">Todos los estados</option>
                <option value="activo">Activos</option>
                <option value="pendiente">Pendientes</option>
                <option value="inactivo">Inactivos</option>
                <option value="sin_membresia">Sin membresía</option>
              </select>
            </div>

            <summary>
              {filtrosAbiertos ? "Cerrar filtros" : "Abrir filtros"}
            </summary>
          </details>

          <div className="bloque estirado">
            <div className="listay3">
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

              {cargando ? (
                <>
                  <Socio carga />
                  <Socio carga />
                  <Socio carga />
                  <Socio carga />
                </>
              ) : error ? (
                <p role="alert">{error}</p>
              ) : respuesta.length === 0 ? (
                <p>No hay socios registrados.</p>
              ) : sociosFiltrados.length === 0 ? (
                <p>No se encontraron socios con esos filtros.</p>
              ) : (
                sociosFiltrados.map((socio) => (
                  <Socio
                    key={socio.codigo_credencial}
                    socio={socio}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Socios;
