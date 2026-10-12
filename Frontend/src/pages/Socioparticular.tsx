import NavBar from "../components/Navbar";
import Icon from "../components/Icon";
import Main from "../components/Main";
import { Link } from "react-router-dom";

type SocioData = {
  id_socio: number;
  id_usuario: string | null;
  nombre: string;
  apellido: string;
  id_sede: number;
  id_plan: number;
  fecha_alta: string;
  estado: string;
  telefono: string;
  dni: string;
};

type Props = {
  socio: SocioData;
};

function Socioparticular({ socio }: Props) {
  const [año, mes, dia] = socio.fecha_alta.split("-");
const meses = [
  "Enero", "Febrero", "Marzo", "Abril",
  "Mayo", "Junio", "Julio", "Agosto",
  "Septiembre", "Octubre", "Noviembre", "Diciembre"
];
  return (
    <Main>
       <header className="h2">
          <h1>Mi socio</h1>
          <Link to="/socios" className="circuloazul2">
            <Icon tipo={18} tamaño={2} />
          </Link>
        </header>
      <section>
       

        <div className="listabloques">
          <div className="bloque4">
            <div className="cuadrado2 iconoestado4"></div>

            <h4>
              {socio.nombre} {socio.apellido}
            </h4>

            <div>Socio: {socio.id_socio}</div>

            <div className="listay2">
              <label>DNI</label>
              <div className="finput">{socio.dni}</div>

              <label>Fecha de alta</label>
              <div className="inputfecha2">
                <div className="finput">{dia}</div>
                <p>/</p>
                <div className="finput">{meses[Number(mes) - 1]}</div>
                <p>/</p>
                <div className="finput">{año}</div>
              </div>
              <label>Estado</label>
              <div className="finput">{socio.estado}</div>

              <label>Sede</label>
              <div className="finput">{socio.id_sede}</div>

              <label>Plan</label>
              <div className="finput">{socio.id_plan}</div>

              <label>Teléfono</label>
              <a
                href={`tel:${socio.telefono}`}
                className="azul2"
              >
                {socio.telefono}
              </a>

              <a
                href={`https://wa.me/54${socio.telefono.replace(/\D/g, "").replace(/^54/, "")}`}
                className="azul2"
                target="_blank"
                rel="noreferrer"
              >
                WhatsApp
              </a>
            </div>

            <br />

            <a href="" className="rojo">
              Dar de baja socio
            </a>
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Socioparticular;
