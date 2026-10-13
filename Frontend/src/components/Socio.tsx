import Icon from "./Icon";
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

type SocioProps = {
  socio?: SocioData;
  carga?: boolean;
  inasistencias?: number;
  sede?: string;
};

function Socio({
  socio,
  carga = false,
  inasistencias = 0,
  sede,
}: SocioProps) {
  const nombre = socio
    ? `${socio.nombre} ${socio.apellido}`
    : "";

  const nombreSede =
    sede ?? (socio ? `Sede ${socio.id_sede}` : "");

  const telefonoLimpio = socio?.telefono.replace(/\D/g, "") ?? "";
  const telefonoWhatsApp = telefonoLimpio.replace(/^54/, "");

  return (
    <article
      className={`rectangulo ${
        inasistencias >= 10 ? "borderojo" : ""
      } ${carga ? "cargando" : ""}`}
    >
      <div className="divisorx">
        {/* Foto */}
        <div
          className={`cuadrado ${
            inasistencias >= 10 ? "iconoestado2" : "iconoestado4"
          } iconoperfil`}
        >
          <Icon
            tipo={2}
            color={inasistencias >= 10 ? 4 : 0}
            tamaño={3.6}
          />
        </div>

        {/* Nombre y sede */}
        <div className="texto2">
          <h4>{nombre}</h4>

          <div className="divisorx2">
            <Icon tipo={14} color={0} tamaño={1.3} />
            <p>{nombreSede}</p>
          </div>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Fecha de alta</h4>
          <p>{socio?.fecha_alta ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>DNI</h4>
          <p>{socio?.dni ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Teléfono</h4>
          <p>{socio?.telefono ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Plan</h4>
          <p>{socio?.id_plan ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Estado</h4>
          <p>{socio?.estado ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Faltas</h4>
          <p>{inasistencias}</p>
        </div>
      </div>


      {/* Acciones para PC */}
      {socio && (
        < div className="divisorx pc">
          <div className="barra"></div>

          <a
            href={`email:`}
            className="circuloazul"
            aria-label={`Llamar a ${nombre}`}
          >
            <Icon tipo={15} tamaño={2} />
          </a>
          <a
            href={`tel:${socio.telefono}`}
            className="circuloazul"
            aria-label={`Llamar a ${nombre}`}
          >
            <Icon tipo={16} tamaño={2} />
          </a>

          <a
            href={`https://wa.me/54${telefonoWhatsApp}`}
            className="circuloazul"
            target="_blank"
            rel="noreferrer"
            aria-label={`Contactar por WhatsApp a ${nombre}`}
          >
            <Icon tipo={17} tamaño={2} />
          </a>
          <div className="barra"></div>
 <a
            className="circulorojo"
          >
            <Icon tipo={20} tamaño={2} />
          </a>
          
        </div>
      )}

      {/* Acceso al detalle en móvil */}
      {socio && (
        <Link
          className="botoncuadrado mobile"
          to={`/socios/${socio.id_socio}`}
        >
          <Icon tipo={13} tamaño={3} />
        </Link>
      )}
    </article>
  );
}

export default Socio;