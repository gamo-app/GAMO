import Icon from "./Icon"
import { Link } from "react-router-dom";
function Socio({ nombre="", sede="",inasistencias=2, carga=false, id=0 }) {
  
  return (
   <article className={`rectangulo ${inasistencias >= 10 ? "borderojo" : ""} ${carga ? "cargando" : ""}`}>
      <div className="divisorx">
     <div className={`cuadrado ${inasistencias >= 10 ? "iconoestado2" : "iconoestado4"} iconoperfil`}>
        <Icon tipo={2} color={inasistencias >= 10 ? 4 : 0} tamaño={3.6}></Icon>

        </div>

        <div className="texto2">
          <h4>{nombre}</h4>
            <div className="divisorx2">
            <Icon tipo={14} color={0} tamaño={1.3}></Icon>
            <p>{sede} - Faltas: {inasistencias}</p> 

            </div>
        </div>
      </div>


    {/*<div className="divisorx3">
      <a href="" className="circuloazul">
      <Icon tipo={15} tamaño={2}></Icon>
    </a>
     <a href="" className="circuloazul">
      <Icon tipo={16} tamaño={2}></Icon>
    </a>
     <a href="" className="circuloazul">
      <Icon tipo={17} tamaño={2}></Icon>
    </a>
    </div>*/}
     {<Link className="botoncuadrado" to={"/socios/"+id}><Icon tipo={13} tamaño={3}></Icon></Link>}
    
       
    </article>
  );
}

export default Socio;