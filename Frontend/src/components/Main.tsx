import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { storage } from "../storage/Storage";

interface MainProps {
  children: ReactNode;
}

function Main({ children }: MainProps) {
  const location = useLocation();
  const modoOscuro = storage.get<boolean>("modoOscuro") ?? false;

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