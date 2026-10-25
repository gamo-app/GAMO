import NavBar from "../components/Navbar";
import Main from "../components/Main";
import Header from "../components/Header";
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
            <div className="cuadrado2 iconoestado4"></div>

            <h4>{nombre}</h4>
            <div>Socio: {socio.codigo_credencial}</div>

            <div className="listay2">
              <label>DNI</label>
              <div className="finput">{socio.usuario?.DNI ?? "-"}</div>

              <label>Fecha de nacimiento</label>
              <div className="finput">
                {socio.usuario?.fecha_nacimiento ?? "-"}
              </div>

              <label>Estado</label>
              <div className="finput">{estado.replace("_", " ")}</div>

              <label>Plan</label>
              <div className="finput">
                {membresia?.plan?.nombre ?? "-"}
              </div>

              <label>Inicio de membresía</label>
              <div className="finput">{membresia?.fecha_inicio ?? "-"}</div>

              <label>Fin de membresía</label>
              <div className="finput">{membresia?.fecha_fin ?? "-"}</div>
            </div>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Socioparticular;
