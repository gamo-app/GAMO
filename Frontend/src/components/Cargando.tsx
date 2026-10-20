
import { createRoot } from "react-dom/client";

export function carga() {
  const contenedor = document.createElement("div");
  document.body.appendChild(contenedor);

  const root = createRoot(contenedor);

  function Cargando() {
    return (
      <div className="alerta-fondo">
        <img src="/cargando.svg" alt="Cargando..." className="cargando" />
      </div>
    );
  }

  root.render(<Cargando />);

  // Devuelve la función para cerrar la pantalla
  return function cerrar() {
    root.unmount();
    contenedor.remove();
  };
}
