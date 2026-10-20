import NavBar from "../components/Navbar";
import Header from "../components/Header";
import { useNavigate } from "react-router-dom";
import { storage } from "../database/Storage";
import { confirmar } from "../components/Alerta";
import { useState } from "react";

function User() {
  const navigate = useNavigate()
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

            <button  className="rojo" onClick={ (e)=>{
               e.preventDefault();

          confirmar(
          "Vas a cerrar la sesión actual ¿Querés continuar?",
          () => {
            navigate("/");
            storage.clear();
          })
            }

            }
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