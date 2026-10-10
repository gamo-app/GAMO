import Home from "../assets/svg/home.svg?raw";
import Calendario from "../assets/svg/calendario.svg?raw";
import Usuario from "../assets/svg/usuario.svg?raw";
import Lupa from "../assets/svg/lupa.svg?raw";
import Qr from "../assets/svg/qr.svg?raw";
import Reloj1 from "../assets/svg/reloj1.svg?raw";
import Reloj2 from "../assets/svg/reloj2.svg?raw";
import Tilde from "../assets/svg/tilde.svg?raw";
import Equis from "../assets/svg/equis.svg?raw";
import Logomini from "../assets/svg/logomini.svg?raw";
import Logo from "../assets/svg/logo.svg?raw";
import Socio from "../assets/svg/socios.svg?raw";
import Triste from "../assets/svg/triste.svg?raw";
import Puntos from "../assets/svg/puntos.svg?raw";
import Ubicacion from "../assets/svg/ubicacion.svg?raw";
import Correo from "../assets/svg/correo.svg?raw";
import WhatsApp from "../assets/svg/whatsapp.svg?raw";
import Telefono from "../assets/svg/telefono.svg?raw";
import Atras from "../assets/svg/atras.svg?raw";
import Notificacion from "../assets/svg/notificaciones.svg?raw";

interface IconProps {
  tipo?: number;
  color?: number;
  tamaño?: number;
}

function Icon({
  tipo = 0,
  color,
  tamaño = 2.6,
}: IconProps) {

  const iconos = [
    Home,         //0
    Calendario,   //1
    Usuario,      //2
    Lupa,         //3
    Qr,           //4
    Reloj1,       //5
    Reloj2,       //6
    Tilde,        //7
    Equis,        //8
    Logomini,     //9
    Logo,         //10
    Socio,        //11
    Triste,       //12
    Puntos,       //13
    Ubicacion,    //14
    Correo,       //15
    WhatsApp,     //16
    Telefono,     //17
    Atras,        //18
    Notificacion ,//19
  ];

  const colores = [
    "var(--grisoscuro)",
    "var(--azul)",
    "var(--siempreblanco)",
    "var(--amarillo)",
    "var(--rojo)",
    "var(--verde)",
  ];

  const imagen = iconos[tipo];

  // Si se especificó un color
  if (color !== undefined) {
    const svg = imagen
      .replaceAll("currentColor", colores[color])
      .replace(
        "<svg",
        `<svg width="${tamaño}vh" height="${tamaño}vh"`
      );

    return (
      <span
        className="icon"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    );
  }

  // Si NO se especificó color
  return (
    <img
      src={`data:image/svg+xml,${encodeURIComponent(imagen)}`}
      alt=""
      className="icon"
      style={{
        width: `${tamaño}vh`,
      }}
    />
  );
}

export default Icon;