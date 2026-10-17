import NavBar from "../components/Navbar";
import Main from "../components/Main";
import Header from "../components/Header";
import type { SocioData } from "../database/Api";

type Props = {
  socio: SocioData;
  onCambiarEstado?: (socio: SocioData) => void;
};

function Socioparticular({ socio, onCambiarEstado }: Props) {
  const fechaPartes = (socio.fecha_alta ?? "").split("-");
  const año = fechaPartes[0] || "-";
  const mes = fechaPartes[1] || "";
  const dia = fechaPartes[2] || "-";

  const meses = [
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre",
  ];

  const nombreMes = mes ? meses[Number(mes) - 1] ?? "-" : "-";
  const telefonoLimpio = (socio.telefono ?? "").replace(/\D/g, "").replace(/^54/, "");

  return (
    <Main>
      <Header atras={true} />
      <section>
        <div className="listabloques">
          <div className="bloque4">
            <div className="cuadrado2 iconoestado4"></div>

            <h4>
              {socio.nombre} {socio.apellido}
            </h4>

            <div>
              Socio: {socio.id_socio}{" "}
              {socio.codigo_credencial ? `(${socio.codigo_credencial})` : ""}
            </div>

            <div className="listay2">
              <label>DNI</label>
              <div className="finput">{socio.dni ?? "-"}</div>

              <label>Correo electrónico</label>
              <div className="finput">{socio.email ?? "Sin email"}</div>

              <label>Fecha de alta</label>
              <div className="inputfecha2">
                <div className="finput">{dia}</div>
                <p>/</p>
                <div className="finput">{nombreMes}</div>
                <p>/</p>
                <div className="finput">{año}</div>
              </div>

              <label>Estado</label>
              <div className="finput">{socio.estado ?? "-"}</div>

              <label>Plan</label>
              <div className="finput">{socio.plan ?? "Sin plan"}</div>

              <label>Estado de cuota</label>
              <div className="finput">
                {socio.estado_cuota ?? "sin_cuota"}
                {socio.monto_cuota != null ? ` ($${socio.monto_cuota})` : ""}
              </div>

              <label>Vencimiento de cuota</label>
              <div className="finput">
                {socio.fecha_vencimiento ?? "Sin vencimiento"}
              </div>

              {socio.telefono && (
                <>
                  <label>Teléfono</label>
                  <a href={`tel:${socio.telefono}`} className="azul2">
                    {socio.telefono}
                  </a>

                  <a
                    href={`https://wa.me/54${telefonoLimpio}`}
                    className="azul2"
                    target="_blank"
                    rel="noreferrer"
                  >
                    WhatsApp
                  </a>
                </>
              )}
            </div>

            <br />

            {onCambiarEstado && (
              <button
                type="button"
                className="rojo"
                style={{
                  width: "100%",
                  height: "5vh",
                  borderRadius: "3vh",
                  backgroundColor: "var(--rojo)",
                  color: "var(--siempreblanco)",
                }}
                onClick={() => onCambiarEstado(socio)}
              >
                {socio.estado === "inactivo"
                  ? "Reactivar socio"
                  : "Dar de baja socio"}
              </button>
            )}
          </div>
        </div>
      </section>

      <NavBar />
    </Main>
  );
}

export default Socioparticular;