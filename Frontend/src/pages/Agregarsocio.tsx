
import NavBar from "../components/Navbar";
import Icon from "../components/Icon";
import Main from "../components/Main";
import { Link, useNavigate } from "react-router-dom";
import { getPlanes, setSocio } from "../database/Api";
import type { PlanSocio } from "../database/Socios";
import { useEffect, useState } from "react";

function Agregarsocio() {
  const navigate = useNavigate();

  const [formulario, setFormulario] = useState({
    nombre: "",
    apellido: "",
    dni: "",
    fecha_nacimiento: "",
    email: "",
    password: "",
    id_plan: "",
    fecha_inicio: "",
    fecha_fin: "",
  });

  const [planes, setPlanes] = useState<PlanSocio[]>([]);
  const [cargandoPlanes, setCargandoPlanes] = useState(true);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let activo = true;

    getPlanes()
      .then((resultado) => {
        if (activo) {
          setPlanes(resultado);
        }
      })
      .catch((error: unknown) => {
        console.error("Error al cargar planes:", error);
        if (activo) {
          setError(
            error instanceof Error
              ? error.message
              : "No se pudieron cargar los planes."
          );
        }
      })
      .finally(() => {
        if (activo) {
          setCargandoPlanes(false);
        }
      });

    return () => {
      activo = false;
    };
  }, []);

  function cambiar(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    const { name, value } = e.target;

    setFormulario((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  }

  async function crearSocio(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setCargando(true);
    setError("");

    try {
      await setSocio({
        usuario: {
          nombre: formulario.nombre,
          apellido: formulario.apellido,
          fecha_nacimiento: formulario.fecha_nacimiento,
          DNI: Number(formulario.dni),
          email: formulario.email,
          password: formulario.password,
        },
        id_plan: Number(formulario.id_plan),
        fecha_inicio: formulario.fecha_inicio,
        fecha_fin: formulario.fecha_fin,
      });

      navigate("/socios");
    } catch (error) {
      console.error("Error al crear socio:", error);
      setError(
        error instanceof Error
          ? error.message
          : "No se pudo crear el socio. Intentá nuevamente."
      );
    } finally {
      setCargando(false);
    }
  }

  return (
    <Main>
      <header className="h2">
        <h1>Agregar socio</h1>

        <Link to="/socios" className="circuloazul2">
          <Icon tipo={18} tamaño={2} />
        </Link>
      </header>

      <section>
        <div className="listabloques">
          <br />

          <div className="bloque4">
            <form onSubmit={crearSocio} className="listay2">
              <label htmlFor="nombre">Nombre</label>
              <input
                className="blanco"
                id="nombre"
                name="nombre"
                type="text"
                placeholder="Nombre del socio"
                value={formulario.nombre}
                onChange={cambiar}
                required
              />

              <label htmlFor="apellido">Apellido</label>
              <input
                className="blanco"
                id="apellido"
                name="apellido"
                type="text"
                placeholder="Apellido del socio"
                value={formulario.apellido}
                onChange={cambiar}
                required
              />

              <label htmlFor="dni">DNI</label>
              <input
                className="blanco"
                id="dni"
                name="dni"
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
                placeholder="Número de DNI"
                value={formulario.dni}
                onChange={cambiar}
                required
              />

              <label htmlFor="fecha_nacimiento">
                Fecha de nacimiento
              </label>
              <input
                className="blanco"
                id="fecha_nacimiento"
                name="fecha_nacimiento"
                type="date"
                value={formulario.fecha_nacimiento}
                onChange={cambiar}
                required
              />

              <label htmlFor="email">Correo electrónico</label>
              <input
                className="blanco"
                id="email"
                name="email"
                type="email"
                placeholder="Correo electrónico"
                value={formulario.email}
                onChange={cambiar}
                required
              />

              <label htmlFor="password">Contraseña</label>
              <input
                className="blanco"
                id="password"
                name="password"
                type="password"
                placeholder="Contraseña"
                autoComplete="new-password"
                value={formulario.password}
                onChange={cambiar}
                required
              />

              <label htmlFor="id_plan">Plan</label>
              <select
                className="blanco"
                id="id_plan"
                name="id_plan"
                value={formulario.id_plan}
                onChange={cambiar}
                required
                disabled={cargandoPlanes || planes.length === 0}
              >
                <option value="">
                  {cargandoPlanes
                    ? "Cargando planes..."
                    : planes.length === 0
                      ? "No hay planes disponibles"
                      : "Seleccionar plan"}
                </option>
                {planes.map((plan) => (
                  <option key={plan.id_plan} value={plan.id_plan}>
                    {plan.nombre} — ${plan.precio_semanal} por semana (
                    {plan.clases_semanales} clases)
                  </option>
                ))}
              </select>

              <label htmlFor="fecha_inicio">Inicio de membresía</label>
              <input
                className="blanco"
                id="fecha_inicio"
                name="fecha_inicio"
                type="date"
                value={formulario.fecha_inicio}
                max={formulario.fecha_fin || undefined}
                onChange={cambiar}
                required
              />

              <label htmlFor="fecha_fin">Fin de membresía</label>
              <input
                className="blanco"
                id="fecha_fin"
                name="fecha_fin"
                type="date"
                value={formulario.fecha_fin}
                min={formulario.fecha_inicio || undefined}
                onChange={cambiar}
                required
              />

              {error && <p className="rojo">{error}</p>}

              <button
                className="azul"
                type="submit"
                disabled={cargando || cargandoPlanes || planes.length === 0}
              >
                {cargando ? "Creando socio..." : "Crear socio"}
              </button>

              <Link to="/socios" className="rojo">
                Cancelar
              </Link>
            </form>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Agregarsocio;
