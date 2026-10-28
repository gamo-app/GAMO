import { useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { storage } from "../storage/Storage";

interface MainProps {
  children: ReactNode;
}

function Main({ children }: MainProps) {
  const location = useLocation();

  const [modoOscuro, setModoOscuro] = useState(
    () => storage.get<boolean>("modoOscuro") ?? false
  );

  useEffect(() => {
    const actualizarModo = () => {
      setModoOscuro(storage.get<boolean>("modoOscuro") ?? false);
    };

    window.addEventListener("modoOscuroCambiado", actualizarModo);

    return () => {
      window.removeEventListener("modoOscuroCambiado", actualizarModo);
    };
  }, []);

  const esLogin =
    location.pathname === "/" || location.pathname === "/crear";

  const clases = [
    esLogin ? "login" : "",
    modoOscuro ? "dark" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return <main className={clases}>{children}</main>;
}

export default Main;