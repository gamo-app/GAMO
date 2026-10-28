
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { storage } from "../storage/Storage";
import Presentacion from "../components/Presentacion";

function Login() {
  const navigate = useNavigate();
  const {
    login,
    usuario,
    cargando: cargandoSesion,
  } = useAuth();

  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const [mostrarPresentacion, setMostrarPresentacion] = useState(
    !storage.exist("presentacionVista")
  );

  useEffect(() => {
    if (cargandoSesion || !usuario) return;

    navigate(
      usuario.primer_ingreso === true
        ? "/contraseña"
        : "/home",
      { replace: true }
    );
  }, [usuario, cargandoSesion, navigate]);

  useEffect(() => {
    if (!mostrarPresentacion) return;

    storage.set("presentacionVista", true);

    const timer = window.setTimeout(() => {
      setMostrarPresentacion(false);
    }, 2500);

    return () => window.clearTimeout(timer);
  }, [mostrarPresentacion]);

  async function handleLogin(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();
    setError("");
    setCargando(true);

    try {
      const usuarioIngresado = await login(correo, contrasena);

      navigate(
        usuarioIngresado.primer_ingreso === true
          ? "/contraseña"
          : "/home",
        { replace: true }
      );
    } catch (error: unknown) {
      setError(
        error instanceof Error
          ? error.message
          : "No se pudo iniciar sesión."
      );
    } finally {
      setCargando(false);
    }
  }

  if (cargandoSesion) {
    return <p>Verificando sesión...</p>;
  }

  if (usuario) {
    return <p>Redirigiendo...</p>;
  }

  return (
    <>
      {mostrarPresentacion && <Presentacion />}

      <section className="login">
        <div className="listabloques">
          <form className="bloque espaciado" onSubmit={handleLogin}>
            <div className="input">
              <label htmlFor="correo">Correo</label>
              <input
                id="correo"
                className="blanco"
                type="email"
                autoComplete="email"
                placeholder="Correo@mail.com"
                value={correo}
                onChange={(event) => setCorreo(event.target.value)}
                required
              />
            </div>

            <div className="input">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                id="contrasena"
                className="blanco"
                type="password"
                autoComplete="current-password"
                placeholder="-----"
                value={contrasena}
                onChange={(event) => setContrasena(event.target.value)}
                required
              />
            </div>

            {error && <p role="alert">{error}</p>}

            <button
              className="azul"
              type="submit"
              disabled={cargando}
            >
              {cargando ? "Iniciando sesión..." : "Iniciar sesión"}
            </button>

            <br />

            <h4>¿No tiene una cuenta?</h4>

            <Link to="/crear" className="blanco">
              Crear cuenta
            </Link>
          </form>
        </div>
      </section>
    </>
  );
}

export default Login;
