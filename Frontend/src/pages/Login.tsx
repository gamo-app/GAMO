
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Header from "../components/Header";
import Main from "../components/Main";
import { useAuth } from "../context/AuthContext";

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(
    e: React.FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();
    setError("");
    setCargando(true);

    try {
      // Inicia sesión y guarda el usuario en AuthContext.
      await login(correo, contrasena);

      // El usuario ya está disponible para Home.
      navigate("/home", { replace: true });
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "No se pudo iniciar sesión."
      );
    } finally {
      setCargando(false);
    }
  }

  return (
    <Main>
      <Header />

      <section className="login">
        <div className="listabloques">
          <form
            className="bloque espaciado"
            onSubmit={handleLogin}
          >
            <div className="input">
              <label htmlFor="correo">Correo</label>

              <input
                id="correo"
                className="blanco"
                type="email"
                autoComplete="email"
                placeholder="Correo@mail.com"
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
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
                onChange={(e) => setContrasena(e.target.value)}
                required
              />
            </div>

            {error && <p role="alert">{error}</p>}

            <button
              className="azul"
              type="submit"
              disabled={cargando}
            >
              {cargando
                ? "Iniciando sesión..."
                : "Iniciar sesión"}
            </button>

            <br />

            <h4>¿No tiene una cuenta?</h4>

            <Link to="/crear" className="blanco">
              Crear cuenta
            </Link>

            <button className="blanco" type="button">
              Iniciar sesión con Google
            </button>
          </form>
        </div>
      </section>
    </Main>
  );
}

export default Login;
