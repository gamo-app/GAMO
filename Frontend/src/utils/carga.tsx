
import { createRoot } from "react-dom/client";

export function carga(): () => void {
  const contenedor = document.createElement("div");
  document.body.appendChild(contenedor);

  const root = createRoot(contenedor);
  let cerrada = false;

  root.render(
    <div className="alerta-fondo">
      <img
        src="/cargando.svg"
        alt="Cargando..."
        className="cargando"
      />
    </div>
  );

  return function cerrar() {
    if (cerrada) return;
    cerrada = true;

    root.unmount();
    contenedor.remove();
  };
}
