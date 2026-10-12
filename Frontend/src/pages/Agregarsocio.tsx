
import NavBar from "../components/Navbar";
import Icon from "../components/Icon";
import Main from "../components/Main";
import { Link, useNavigate } from "react-router-dom";
import { setSocio } from "../database/Api";
import { useState } from "react";

function Agregarsocio() {
  const navigate = useNavigate();

  const [formulario, setFormulario] = useState({
    nombre: "",
    apellido: "",
    dni: "",
    telefono: "",
    fecha_nacimiento: "",
    email: "",
    nombre_usuario: "",
    password: "",
    id_plan: "",
  });

  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

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
        persona: {
          nombre: formulario.nombre,
          apellido: formulario.apellido,
          dni: formulario.dni,
          telefono: formulario.telefono,
          fecha_nacimiento: formulario.fecha_nacimiento,
        },
        usuario: {
          email: formulario.email,
          nombre_usuario: formulario.nombre_usuario,
          password: formulario.password,
        },
        id_plan: Number(formulario.id_plan),
      });

      navigate("/socios");
    } catch (error) {
      console.error("Error al crear socio:", error);
      setError("No se pudo crear el socio. Intentá nuevamente.");
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
                type="text"
                inputMode="numeric"
                placeholder="Número de DNI"
                value={formulario.dni}
                onChange={cambiar}
                required
              />

              <label htmlFor="telefono">Teléfono</label>
              <input
                className="blanco"
                id="telefono"
                name="telefono"
                type="tel"
                placeholder="Número de teléfono"
                value={formulario.telefono}
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

              <label htmlFor="nombre_usuario">Nombre de usuario</label>
              <input
                className="blanco"
                id="nombre_usuario"
                name="nombre_usuario"
                type="text"
                placeholder="Nombre de usuario"
                value={formulario.nombre_usuario}
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
              >
                <option value="">Seleccionar plan</option>
                <option value="1">Plan 1</option>
                <option value="2">Plan 2</option>
              </select>

              {error && <p className="rojo">{error}</p>}

              <button
                className="azul"
                type="submit"
                disabled={cargando}
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
