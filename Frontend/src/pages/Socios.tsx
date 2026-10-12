import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Socio from "../components/Socio";
import Main from "../components/Main";
import Socioparticular from "./Socioparticular";
import { getSocios } from "../database/Api";
import { useState, useEffect } from "react";
import { useParams,Link } from "react-router-dom";

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

  // Estados de los filtros
  const [sede, setSede] = useState("");
  const [estado, setEstado] = useState("");
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");

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

  // Filtrar socios
  const sociosFiltrados = respuesta.filter((socio) => {
    const coincideSede =
      sede === "" || socio.id_sede === Number(sede);

    const coincideEstado =
      estado === "" ||
      socio.estado.toLowerCase() === estado.toLowerCase();

    const coincideNombre = socio.nombre
      .toLowerCase()
      .includes(nombre.trim().toLowerCase());

    const coincideApellido = socio.apellido
      .toLowerCase()
      .includes(apellido.trim().toLowerCase());

    return (
      coincideSede &&
      coincideEstado &&
      coincideNombre &&
      coincideApellido
    );
  });

  if (id) {
    const socio = respuesta.find(
      (s) => s.id_socio === Number(id)
    );

    if (cargando) {
      return <Main>Cargando socio...</Main>;
    }

    if (!socio) {
      return <Main>Socio no encontrado</Main>;
    }

    return <Socioparticular socio={socio} />;
  }

  return (
    <Main>
        <Header />

      <section>

        <div className="listabloques">
          <div className="bloque">
            <Link to="/agregarsocio" className="azul">
                Agregar socio
              </Link>

            <details className="azul">
              <summary>Filtrar socios</summary>

              <div className="listay2">
                <select
                  className="blanco"
                  value={sede}
                  onChange={(e) => setSede(e.target.value)}
                >
                  <option value="">Todas las sedes</option>
                  <option value="1">Sede 1</option>
                  <option value="2">Sede 2</option>
                </select>

                <select
                  className="blanco"
                  value={estado}
                  onChange={(e) => setEstado(e.target.value)}
                >
                  <option value="">Mostrar todos</option>
                  <option value="activo">Activos</option>
                  <option value="inactivo">Inactivos</option>
                </select>

                <div className="divisorx">
                  <input
                    className="blanco"
                    type="text"
                    placeholder="Nombre"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                  />

                  <input
                    className="blanco"
                    type="text"
                    placeholder="Apellido"
                    value={apellido}
                    onChange={(e) => setApellido(e.target.value)}
                  />
                </div>
              </div>
            </details>

            {cargando ? (
              <>
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
                  nombre={`${socio.nombre} ${socio.apellido}`}
                  carga={false}
                  id={socio.id_socio}
                />
              ))
            )}
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Socios;