import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Header from "../components/Header";
import NavBar from "../components/Navbar";
import { useAuth } from "../context/AuthContext";
import { storage } from "../database/Storage";

function User() {
  const navigate = useNavigate();
  const { usuario, logout } = useAuth();
  const [modoOscuro, setModoOscuro] = useState(
    storage.get<boolean>("modoOscuro") ?? false
  );
  const [error, setError] = useState("");

  function cambiarModo(event: React.ChangeEvent<HTMLSelectElement>) {
    const nuevoModo = event.target.value === "true";
    setModoOscuro(nuevoModo);
    storage.set("modoOscuro", nuevoModo);
  }

  async function handleCerrarSesion() {
    setError("");
    try {
      await logout();
      navigate("/", { replace: true });
    } catch (error: unknown) {
      console.error("Error al cerrar sesión:", error);
      setError(
        error instanceof Error
          ? error.message
          : "No se pudo cerrar la sesión en el servidor."
      );
    }
  }

  return (
    <main className={modoOscuro ? "dark" : ""}>
      <Header />
      <section>
        <div className="listabloques">
          <div className="bloque">
            <h2>{usuario ? `${usuario.nombre} ${usuario.apellido}` : "Usuario"}</h2>
            <p>{usuario?.email ?? ""}</p>

            <label htmlFor="modo-oscuro">Apariencia</label>
            <select
              id="modo-oscuro"
              className="blanco"
              value={String(modoOscuro)}
              onChange={cambiarModo}
            >
              <option value="false">Modo claro</option>
              <option value="true">Modo oscuro</option>
            </select>

            {error && <p role="alert">{error}</p>}

            <button
              type="button"
              className="rojo"
              onClick={() => void handleCerrarSesion()}
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </section>
      <NavBar />
    </main>
  );
}

export default User;
