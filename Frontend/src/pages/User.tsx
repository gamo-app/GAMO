import NavBar from "../components/Navbar";
import Header from "../components/Header";
import { Link } from "react-router-dom";
import { storage } from "../database/Storage";

import { useState } from "react";

function User() {
  const [modoOscuro, setModoOscuro] = useState(
    storage.get<boolean>("modoOscuro") ?? false
  );

  
  function cambiarModo(e: React.ChangeEvent<HTMLSelectElement>) {
    const nuevoModo = e.target.value === "true";

    setModoOscuro(nuevoModo);
    storage.set("modoOscuro", nuevoModo);
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

            <Link to="/" className="rojo">
              Cerrar sesión
            </Link>
          </div>

         
        </div>
      </section>

      <NavBar />
    </main>
  );
}

export default User;