import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Socio from "../components/Socio";
import Main from "../components/Main";
import Socioparticular from "./Socioparticular";
import { getSocios } from "../database/Api";
import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import Icon from "../components/Icon";
import { evaluarMembresia, type SocioListado } from "../database/Socios";

function Socios() {
  const { id } = useParams();

  const [respuesta, setRespuesta] = useState<SocioListado[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  // Filtros
  const [busqueda, setBusqueda] = useState("");
  const [estado, setEstado] = useState("");

  useEffect(() => {
    getSocios()
      .then((resultado) => {
        setRespuesta(resultado);
      })
      .catch((error) => {
        console.error("Error al cargar socios:", error);
        setError("No se pudieron cargar los socios. Intentá nuevamente.");
      })
      .finally(() => {
        setCargando(false);
      });
  }, []);

  // Buscar por nombre, apellido o DNI
  const sociosFiltrados = respuesta.filter((socio) => {
    const texto = busqueda.trim().toLowerCase();
    const nombre = socio.usuario
      ? `${socio.usuario.nombre} ${socio.usuario.apellido}`.toLowerCase()
      : "";
    const dni = socio.usuario ? String(socio.usuario.DNI) : "";
    const estadoSocio = evaluarMembresia(socio.membresias).estado;

    const coincideBusqueda =
      texto === "" ||
      nombre.includes(texto) ||
      dni.includes(texto);

    const coincideEstado =
      estado === "" ||
      estadoSocio === estado;

    return coincideBusqueda && coincideEstado;
  });

  if (id) {
    if (cargando) {
      return <Main>Cargando socio...</Main>;
    }

    const socio = respuesta.find((s) => s.codigo_credencial === id);

    if (!socio) {
      return <Main>Socio no encontrado</Main>;
    }

    return <Socioparticular socio={socio} />;
  }

  const cambiarEstado = (nuevoEstado: string) => {
    setEstado(nuevoEstado);
  };

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
                placeholder="Buscar nombre, apellido o DNI..."
                value={busqueda}
                onChange={(event) => setBusqueda(event.target.value)}
              />
              <button className="botoniconoazul">
                <Icon tipo={3} color={2} />
                Buscar
              </button>
            </div>

            <div className="divisorx espaciado2">
              <Link to="/agregarsocio" className="azul pc">
                Agregar nuevo socio
              </Link>
            </div>

            <div className="listax overflow">
              <div className="contenidolista">
                {[
                  { texto: "Todos", valor: "" },
                  { texto: "Pendientes", valor: "pendiente" },
                  { texto: "Inactivos", valor: "inactivo" },
                  { texto: "Activos", valor: "activo" },
                  { texto: "Sin membresía", valor: "sin_membresia" },
                ].map((filtro) => (
                  <button
                    key={filtro.texto}
                    type="button"
                    className={`${
                      estado === filtro.valor ? "azul" : "blanco"
                    } miniboton`}
                    onClick={() => cambiarEstado(filtro.valor)}
                  >
                    {filtro.texto}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="bloque estirado">
            {cargando ? (
              <>
                <Socio carga={true} />
                <Socio carga={true} />
                <Socio carga={true} />
                <Socio carga={true} />
                <Socio carga={true} />
              </>
            ) : error ? (
              <div className="listay" role="alert">
                <p>{error}</p>
              </div>
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
                  key={socio.codigo_credencial}
                  socio={socio}
                  carga={false}
                />
              ))
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