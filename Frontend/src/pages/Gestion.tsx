import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Socio from "../components/Socio";
import Main from "../components/Main";
import Icon from "../components/Icon"
import Error from "../pages/404"
import { LIMITE_REGISTROS } from "../database/Config";
import Socioparticular from "./Socioparticular";
import {
  getSocios,
  getProfesores,
  getRepresentantes,
  getAdmins,
} from "../database/Api";
import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

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

function Socios() {
  const { id } = useParams();

const [limite, setLimite] = useState(LIMITE_REGISTROS);
  const [respuesta, setRespuesta] = useState<SocioData[]>([]);
  const [cargando, setCargando] = useState(true);
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(false);

  // Filtros
  const [busqueda, setBusqueda] = useState("");
  const [sede, setSede] = useState("");
  const [estado, setEstado] = useState("");
  const [tipo, setTipo] = useState<Tipo>("socios");

useEffect(() => {
  setLimite(LIMITE_REGISTROS);
}, [busqueda, sede, estado, tipo]);
  useEffect(() => {
    let cancelado = false;

    async function cargarDatos() {
      setCargando(true);

      try {
        let resultado: SocioData[];

        switch (tipo) {
          case "profesores":
            resultado = await getProfesores<SocioData[]>();
            break;
          case "representantes":
            resultado = await getRepresentantes<SocioData[]>();
            break;
          case "admins":
            resultado = await getAdmins<SocioData[]>();
            break;
          default:
            resultado = await getSocios<SocioData[]>();
        }

        if (!cancelado) {
          setRespuesta(Array.isArray(resultado) ? resultado : []);
        }
      } catch (error) {
        console.error("Error al cargar datos:", error);

        if (!cancelado) {
          setRespuesta([]);
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
  }, [tipo]);

  // Buscar por nombre, apellido, DNI o teléfono
  const sociosFiltrados = respuesta.filter((socio) => {
    const texto = busqueda.trim().toLowerCase();

    const coincideBusqueda =
      texto === "" ||
      `${socio.nombre ?? ""} ${socio.apellido ?? ""}`
        .toLowerCase()
        .includes(texto) ||
      `${socio.apellido ?? ""} ${socio.nombre ?? ""}`
        .toLowerCase()
        .includes(texto) ||
      String(socio.dni ?? "").toLowerCase().includes(texto) ||
      String(socio.telefono ?? "").toLowerCase().includes(texto);

    const coincideSede =
      sede === "" || String(socio.id_sede) === sede;

    const estadoSocio = String(socio.estado ?? "")
      .toLowerCase()
      .trim();

    const coincideEstado =
      estado === "" ||
      (estado === "morosos"
        ? false // Requiere un dato real de deuda.
        : estadoSocio === estado);

    return coincideBusqueda && coincideSede && coincideEstado;
  });
const sociosVisibles = sociosFiltrados.slice(0, limite);
  if (id && tipo === "socios") {
    if (cargando) {
      return <Main>Cargando socio...</Main>;
    }

    const socio = respuesta.find(
      (s) => s.id_socio === Number(id)
    );

    if (!socio) {
      return <Error></Error>;
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
         <details
  className="bloque persistente estirado"
  onToggle={(e) => setFiltrosAbiertos(e.currentTarget.open)}
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
              />

              <button
                type="button"
                className="azul buscar"
                
                onClick={() => setBusqueda(busqueda.trim())}
              >
                <Icon tipo={3} tamaño={1.8} color={2}></Icon>
              Buscar
              </button>
            </div>

            <div className="divisorxy espaciado2">
              <select
                className="blanco"
                value={tipo}
                onChange={(e) => {
                  setTipo(e.target.value as Tipo);
                  setSede("");
                  setEstado("");
                }}
              >
                <option value="socios">Socios</option>
                <option value="profesores">Profesores</option>
                <option value="representantes">Representantes</option>
                <option value="admins">Administradores</option>
              </select>

              <select
                className="blanco"
                value={estado}
                onChange={(e) => cambiarEstado(e.target.value)}
              >
                {[
                  { texto: "Todos", valor: "" },
                  { texto: "Morosos", valor: "morosos" },
                  { texto: "Inactivos", valor: "inactivo" },
                  { texto: "Activos", valor: "activo" },
                ].map((filtro) => (
                  <option key={filtro.texto} value={filtro.valor}>
                    {filtro.texto}
                  </option>
                ))}
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
          <div className={respuesta.length === 0 || sociosFiltrados.length === 0 ? "listay" : "listay3"}>
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
              ) : respuesta.length === 0 ? (
                <>
                <br />
                <br />
                <br />
                  <Icon tipo={12} tamaño={10}></Icon>
                <p>No hay registros disponibles.</p>
</>
              ) : sociosFiltrados.length === 0 ? (
                <div className="listay">
                   <br />
                <br />
                <br />
                  <Icon tipo={12} tamaño={10}></Icon>

 <p>No se encontraron registros con esos filtros.</p>
                </div>
               
              ) : (
                <>
  {sociosVisibles.map((socio) => (
    <Socio
      key={socio.id_socio}
      socio={socio}
      carga={false}
    />
  ))}

 
</>
              )}
            </div>
          </div>
           {limite < sociosFiltrados.length && (
    <button
      type="button"
      className="azul"
      onClick={() => setLimite((anterior) => anterior + LIMITE_REGISTROS)}
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

export default Socios;