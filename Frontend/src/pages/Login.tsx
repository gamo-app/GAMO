
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "../components/Header";
import Main from "../components/Main";
import { iniciarSesion } from "../database/Api";

function Login() {
  const navigate = useNavigate();

  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setCargando(true);

    try {
      const respuesta = await iniciarSesion({
        email: correo,
        password: contrasena,
      });

      console.log("Inicio de sesión correcto:", respuesta);

      navigate("/home");
    } catch (error) {
      console.error("Error al iniciar sesión:", error);
      setError("Correo o contraseña incorrectos.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <Main>
      <Header />

      <section className="login">
        <div className="listabloques">
          <form className="bloque" onSubmit={handleLogin}>
            <label htmlFor="correo">Correo</label>
            <input
              id="correo"
              className="blanco"
              type="email"
              placeholder="Correo@mail.com"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              required
            />

            <label htmlFor="contrasena">Contraseña</label>
            <input
              id="contrasena"
              className="blanco"
              type="password"
              placeholder="-----"
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
              required
            />

            {error && <p role="alert">{error}</p>}

            <button className="azul" type="submit" disabled={cargando}>
              {cargando ? "Iniciando sesión..." : "Iniciar sesión"}
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