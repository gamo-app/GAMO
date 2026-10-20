
import { createRoot } from "react-dom/client";
import Icon from "./Icon";
export function confirmar(mensaje: string, accion: () => void) {
  const contenedor = document.createElement("div");
  document.body.appendChild(contenedor);

  const root = createRoot(contenedor);

  function cerrar() {
    root.unmount();
    contenedor.remove();
  }

  function Alerta() {
    return (
      <div className="alerta-fondo">
           <Icon tipo={23} tamaño={15} ></Icon>

        <div className="alerta">

          <h3 className="centro">¿Estás seguro?</h3>
          <p className="centro">{mensaje}</p>

          <div className="divisorx">
            <button
              className="rojo"
              onClick={cerrar}
            >
              No
            </button>

            <button
              className="azul"
              onClick={() => {
                cerrar();
                accion();
              }}
            >
              Sí, continuar
            </button>
          </div>
        </div>
      </div>
    );
  }

  root.render(<Alerta />);
}
