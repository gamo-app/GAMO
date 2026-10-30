import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";


import { getPlanes, setSocio } from "../api/Api";
import type { PlanSocio } from "../api/Socios";

type FormularioSocio = {
  nombre: string;
  apellido: string;
  dni: string;
  fecha_nacimiento: string;
  email: string;
  password: string;
  id_plan: string;
  fecha_inicio: string;
  fecha_fin: string;
};

function Agregarsocio() {
  const navigate = useNavigate();
  const { tipo = "socio" } = useParams();
  const esAltaSocio = tipo === "socio";

  const [formulario, setFormulario] = useState<FormularioSocio>({
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

    if (!esAltaSocio) {
      return () => {
        activo = false;
      };
    }

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
  }, [esAltaSocio]);

  function cambiar(
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    const { name, value } = event.target;
    setFormulario((anterior) => ({ ...anterior, [name]: value }));
  }

  async function crearSocio(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCargando(true);
    setError("");

    try {
      await setSocio({
        usuario: {
          nombre: formulario.nombre.trim(),
          apellido: formulario.apellido.trim(),
          fecha_nacimiento: formulario.fecha_nacimiento,
          DNI: Number(formulario.dni),
          email: formulario.email.trim(),
          password: formulario.password,
        },
        id_plan: Number(formulario.id_plan),
        fecha_inicio: formulario.fecha_inicio,
        fecha_fin: formulario.fecha_fin,
      });

      navigate("/gestion");
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
    <>
   

      <section>
        <div className="listabloques">
          <div className="bloque4 espaciado">
            {esAltaSocio ? (
              <form onSubmit={crearSocio} className="listay2">
                <label htmlFor="nombre">Nombre</label>
                <input
                  className="blanco"
                  id="nombre"
                  name="nombre"
                  type="text"
                  autoComplete="given-name"
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
                  autoComplete="family-name"
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
                  autoComplete="email"
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
                  autoComplete="new-password"
                  minLength={8}
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
                  disabled={cargandoPlanes || planes.length === 0}
                  required
                >
                  <option value="">
                    {cargandoPlanes
                      ? "Cargando planes..."
                      : planes.length
                        ? "Seleccionar plan"
                        : "No hay planes disponibles"}
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

                {error && <p role="alert">{error}</p>}

                <button
                  className="azul"
                  type="submit"
                  disabled={
                    cargando ||
                    cargandoPlanes ||
                    planes.length === 0
                  }
                >
                  {cargando ? "Creando socio..." : "Crear socio"}
                </button>
              </form>
            ) : (
              <p role="alert">
                La creación de usuarios de tipo “{tipo}” todavía no está
                disponible en el backend actual.
              </p>
            )}

            <Link to="/gestion" className="rojo">
              Cancelar
            </Link>
          </div>
        </div>
      </section>

  
    </>
  );
}

export default Agregarsocio;
