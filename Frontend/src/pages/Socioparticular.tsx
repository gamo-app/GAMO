import { Link } from "react-router-dom";

import Header from "../components/Header";
import Main from "../components/Main";
import NavBar from "../components/Navbar";
import { evaluarMembresia, type SocioListado } from "../database/Socios";

type Props = {
  socio: SocioListado;
};

function Socioparticular({ socio }: Props) {
  const { estado, membresia } = evaluarMembresia(socio.membresias);
  const nombre = socio.usuario
    ? `${socio.usuario.nombre} ${socio.usuario.apellido}`
    : "Usuario no disponible";

  return (
    <Main>
      <Header atras />

      <section>
        <div className="listabloques">
          <div className="bloque4">
            <div className="cuadrado2 iconoestado4">
              <span aria-hidden="true">
                {nombre.slice(0, 1).toLocaleUpperCase()}
              </span>
            </div>

            <h4>{nombre}</h4>
            <p>Credencial: {socio.codigo_credencial}</p>

            <div className="listay2">
              <label>DNI</label>
              <div className="finput">{socio.usuario?.DNI ?? "-"}</div>

              <label>Fecha de nacimiento</label>
              <div className="finput">
                {socio.usuario?.fecha_nacimiento ?? "-"}
              </div>

              <label>Estado de membresía</label>
              <div className="finput">{estado.replace("_", " ")}</div>

              <label>Plan</label>
              <div className="finput">
                {membresia?.plan?.nombre ?? "Sin membresía"}
              </div>

              <label>Inicio de membresía</label>
              <div className="finput">
                {membresia?.fecha_inicio ?? "-"}
              </div>

              <label>Fin de membresía</label>
              <div className="finput">
                {membresia?.fecha_fin ?? "-"}
              </div>
            </div>

            <Link to="/socios" className="azul2">
              Volver a socios
            </Link>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Socioparticular;
