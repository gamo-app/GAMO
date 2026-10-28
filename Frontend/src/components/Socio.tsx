import { Link } from "react-router-dom";

import Icon from "./Icon";
import { evaluarMembresia, type SocioListado } from "../api/Socios";

type SocioProps = {
  socio?: SocioListado;
  carga?: boolean;
};

function Socio({ socio, carga = false }: SocioProps) {
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
        <div className={`cuadrado iconoestado4 iconoperfil`}>
          <Icon
            tipo={2}
            color={0}
            tamaño={3.6}
          />
        </div>

        <div className="texto2">
          <div className="listax2">
            <h4>{nombre}</h4>
            {carga ? <></>: <div className={estado === "inactivo" ? "circulo rojo" : "circulo verde"}></div>}
            
           
          </div>
         
          <div className="divisorx3">
            <p>{membresia?.plan?.nombre ?? "Sin membresía"}</p>

    
          </div>
        </div>
      </div>

      {socio && (
        <Link
          className="botoncuadrado"
          to={`/perfil/${socio.codigo_credencial}`}
          aria-label={`Ver detalles de ${nombre}`}
        >
          <Icon tipo={13} tamaño={3} />
        </Link>
      )}
    </article>
  );
}

export default Socio;
