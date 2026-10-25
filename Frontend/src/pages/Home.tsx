import { useEffect, useRef } from "react";
import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Main from "../components/Main";
import { useAuth } from "../context/AuthContext";

function Home() {
  const { usuario, cargando } = useAuth();
  const usuarioRegistrado = useRef<string | null>(null);

  useEffect(() => {
    if (
      usuario &&
      usuarioRegistrado.current !== usuario.uuid_usuario
    ) {
      console.log("Usuario recibido en Home:", usuario);
      usuarioRegistrado.current = usuario.uuid_usuario;
    }
  }, [usuario]);

  if (cargando) {
    return <p>Cargando usuario...</p>;
  }

  if (!usuario) {
    return <p>No se encontró un usuario autenticado.</p>;
  }

  return (
    <Main>
      <Header />

      <section>
        <div className="listabloques">
          <div className="listacentro">
            <img
              src="proceso.svg"
              className="proceso"
              style={{ width: "12vh" }}
              alt=""
            />
            <h3>En proceso</h3>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Home;