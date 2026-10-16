import { useState } from "react";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/Navbar";
import Header from "../components/Header";
import { storage } from "../database/Storage";
import { cerrarSesion } from "../database/Api";

function User() {
  const [modoOscuro, setModoOscuro] = useState(
    storage.get<boolean>("modoOscuro") ?? false
  );

  const navigate = useNavigate();

  function cambiarModo(e: React.ChangeEvent<HTMLSelectElement>) {
    const nuevoModo = e.target.value === "true";

    setModoOscuro(nuevoModo);
    storage.set("modoOscuro", nuevoModo);
  }

  async function handleCerrarSesion() {
    try {
      await cerrarSesion();
    } catch (error) {
      console.error("Error al cerrar sesión en el servidor:", error);
    } finally {
      // Eliminar los datos locales de autenticación.
      storage.remove("sesion");

      // Volver al login.
      navigate("/", { replace: true });
    }
  }

  return (
    <main className={modoOscuro ? "dark" : ""}>
      <Header />

      <section>
        <div className="listabloques">
          <div className="bloque">
            <select
              className="blanco"
              value={String(modoOscuro)}
              onChange={cambiarModo}
            >
              <option value="false">Modo claro</option>
              <option value="true">Modo oscuro</option>
            </select>

            <button
              type="button"
              className="rojo"
              onClick={handleCerrarSesion}
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