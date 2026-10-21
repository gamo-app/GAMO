
import NavBar from "../components/Navbar";
import Icon from "../components/Icon";
import Main from "../components/Main";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  setSocio,
  setAdmin,
  setUsuarioRecepcion,
} from "../database/Api";
import { useState } from "react";

type TipoUsuario = "socio" | "admin" | "profesor" | "representante";

function Agregarsocio() {
  const navigate = useNavigate();
  const location = useLocation();

  // Detectar el tipo de usuario desde la URL.
  // Si no hay tipo reconocido, se usa socio.
  const partes = location.pathname.split("/").filter(Boolean);
  const ultimoSegmento = partes[partes.length - 1];

  const tipoUsuario: TipoUsuario =
    ultimoSegmento === "admin" ||
    ultimoSegmento === "profesor" ||
    ultimoSegmento === "representante" ||
    ultimoSegmento === "socio"
      ? ultimoSegmento
      : "socio";

  const titulos: Record<TipoUsuario, string> = {
    socio: "Agregar socio",
    admin: "Agregar administrador",
    profesor: "Agregar profesor",
    representante: "Agregar representante",
  };

  const nombreTipo: Record<TipoUsuario, string> = {
    socio: "socio",
    admin: "administrador",
    profesor: "profesor",
    representante: "representante",
  };

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

 
async function crearUsuario(e: React.FormEvent<HTMLFormElement>) {
  e.preventDefault();

  if (cargando) return;

  setCargando(true);
  setError("");

  try {
    const persona = {
      nombre: formulario.nombre.trim(),
      apellido: formulario.apellido.trim(),
      dni: formulario.dni.trim(),
      telefono: formulario.telefono.trim(),
      fecha_nacimiento: formulario.fecha_nacimiento,
    };

    const usuario = {
      email: formulario.email.trim(),
      nombre_usuario: formulario.nombre_usuario.trim(),
      password: formulario.password,
    };

    if (
      !persona.nombre ||
      !persona.apellido ||
      !persona.dni ||
      !persona.telefono ||
      !persona.fecha_nacimiento ||
      !usuario.email ||
      !usuario.nombre_usuario ||
      !usuario.password
    ) {
      setError("Completá todos los campos obligatorios.");
      return;
    }

    if (tipoUsuario === "socio" && !formulario.id_plan) {
      setError("Seleccioná un plan.");
      return;
    }
if (formulario.password.length < 8) {
  setError("La contraseña debe tener al menos 8 caracteres.");
  return;
}
    switch (tipoUsuario) {
      case "socio":
        await setSocio({
          persona,
          usuario,
          id_plan: Number(formulario.id_plan),
        });
        break;

      case "profesor":
        await setUsuarioRecepcion({
          ...persona,
          email: usuario.email,
          password: usuario.password,
          rol: "profesor",
          id_sede: 1,
        });
        break;

      case "representante":
        setError(
          "Falta definir el endpoint de creación de representantes en la API."
        );
        return;

      case "admin":
        await setAdmin({
          ...persona,
          email: usuario.email,
          password: usuario.password,
          rol: "admin",
          id_sede: 1,
        });
        break;
    }

    navigate("/gestion");
  } catch (err) {
    console.error(`Error al crear ${nombreTipo[tipoUsuario]}:`, err);

    setError(
      err instanceof Error
        ? err.message
        : `No se pudo crear el ${nombreTipo[tipoUsuario]}.`
    );
  } finally {
    setCargando(false);
  }
}


  return (
    <Main>
      <header className="h2">
        <h1>{titulos[tipoUsuario]}</h1>

        <Link to="/gestion" className="circuloazul2">
          <Icon tipo={18} tamaño={2} />
        </Link>
      </header>

      <section>
        <div className="listabloques">
          <br />

          <div className="bloque4">
            <form onSubmit={crearUsuario} className="listay2">
              <label htmlFor="nombre">Nombre</label>
              <input
                className="blanco"
                id="nombre"
                name="nombre"
                type="text"
                placeholder="Nombre"
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
                placeholder="Apellido"
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
                placeholder="Contraseña (mínimo 8 caracteres)"
                value={formulario.password}
                onChange={cambiar}
                minLength={8}
                required
              />

              {tipoUsuario === "socio" && (
                <>
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
                </>
              )}

              {error && <p className="rojo">{error}</p>}

              <button
                className="azul"
                type="submit"
                disabled={cargando}
              >
                {cargando
                  ? `Creando ${nombreTipo[tipoUsuario]}...`
                  : `Crear ${nombreTipo[tipoUsuario]}`}
              </button>

              <Link to="/gestion" className="rojo">
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
