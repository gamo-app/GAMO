import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Socio from "../components/Socio";
import Main from "../components/Main";
import Socioparticular from "./Socioparticular";
import { getSocios } from "../database/Api";
import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import Icon from "../components/Icon";
type SocioData = {
  id_socio: number;
  id_usuario: string | null;
  nombre: string;
  apellido: string;
  id_sede: number;
  id_plan: number;
  fecha_alta: string;
  estado: string;
  telefono: string;
  dni: string;
};

function Socios() {
  const { id } = useParams();

  const [respuesta, setRespuesta] = useState<SocioData[]>([]);
  const [cargando, setCargando] = useState(true);

  // Filtros
  const [busqueda, setBusqueda] = useState("");
  const [sede, setSede] = useState("");
  const [estado, setEstado] = useState("");

  useEffect(() => {
    getSocios<SocioData[]>()
      .then((resultado) => {
        setRespuesta(resultado);
      })
      .catch((error) => {
        console.error("Error al cargar socios:", error);
      })
      .finally(() => {
        setCargando(false);
      });
  }, []);

  // Buscar por nombre, apellido, DNI o teléfono
  const sociosFiltrados = respuesta.filter((socio) => {
    const texto = busqueda.trim().toLowerCase();

    const coincideBusqueda =
      texto === "" ||
      `${socio.nombre} ${socio.apellido}`.toLowerCase().includes(texto) ||
      `${socio.apellido} ${socio.nombre}`.toLowerCase().includes(texto) ||
      socio.dni.includes(texto) ||
      socio.telefono.includes(texto);

    const coincideSede =
      sede === "" || socio.id_sede === Number(sede);

    const estadoSocio = socio.estado.toLowerCase().trim();

    const coincideEstado =
      estado === "" ||
      (estado === "morosos"
        ? false // Reemplazar cuando tengas el dato real de deuda
        : estadoSocio === estado);

    return coincideBusqueda && coincideSede && coincideEstado;
  });

  if (id) {
    if (cargando) {
      return <Main>Cargando socio...</Main>;
    }

    const socio = respuesta.find(
      (s) => s.id_socio === Number(id)
    );

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
                placeholder="Buscar nombre, apellido, DNI o teléfono..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
              />
              <button className="botoniconoazul">
                <Icon tipo={3} color={2} ></Icon>

                Buscar
              </button>
            </div>
            <div className="divisorx espaciado2" >
             
              <select  className="blanco" name="" id="">
<option value="">todos</option>
              </select>

              <select
                className="blanco"
                value={sede}
                onChange={(e) => setSede(e.target.value)}
              >
                <option value="">Todas las sedes</option>

                {Array.from(
                  new Set(respuesta.map((socio) => socio.id_sede))
                )
                  .sort((a, b) => a - b)
                  .map((idSede) => (
                    <option key={idSede} value={idSede}>
                      Sede {idSede}
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