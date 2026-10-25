import Icon from "./Icon";
import { Link } from "react-router-dom";
import { evaluarMembresia, type SocioListado } from "../database/Socios";

type SocioProps = {
  socio?: SocioListado;
  carga?: boolean;
};

function Socio({
  socio,
  carga = false,
}: SocioProps) {
  const nombre = socio?.usuario
    ? `${socio.usuario.nombre} ${socio.usuario.apellido}`
    : "Usuario no disponible";
  const { estado, membresia } = socio
    ? evaluarMembresia(socio.membresias)
    : { estado: null, membresia: null };

  return (
    <article
      className={`rectangulo ${
        estado === "inactivo" ? "borderojo" : ""
      } ${carga ? "cargando" : ""}`}
    >
      <div className="divisorx">
        {/* Foto */}
        <div
          className={`cuadrado ${
            estado === "activo" ? "iconoestado4" : "iconoestado2"
          } iconoperfil`}
        >
          <Icon
            tipo={2}
            color={estado === "activo" ? 0 : 4}
            tamaño={3.6}
          />
        </div>

        {/* Nombre y sede */}
        <div className="texto2">
          <h4>{nombre}</h4>
          <div className="divisorx2">
            <Icon tipo={14} color={0} tamaño={1.3} />
            <p>{socio?.codigo_credencial}</p>
          </div>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Inicio de membresía</h4>
          <p>{membresia?.fecha_inicio ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>DNI</h4>
          <p>{socio?.usuario?.DNI ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Plan</h4>
          <p>{membresia?.plan?.nombre ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Estado</h4>
          <p>{estado?.replace("_", " ") ?? "-"}</p>
        </div>
      </div>

      {/* Acceso al detalle en móvil */}
      {socio && (
        <Link
          className="botoncuadrado mobile"
          to={`/socios/${socio.codigo_credencial}`}
        >
          <Icon tipo={13} tamaño={3} />
        </Link>
      )}
    </article>
  );
}

export default Socio;