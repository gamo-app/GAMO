import { useState } from "react";
import type { ReactNode } from "react";
import { storage } from "../database/Storage";
import { useLocation } from "react-router-dom";

interface MainProps {
  children: ReactNode;
}

function Main({ children }: MainProps) {
  const location = useLocation();

  if (!storage.exist("modoOscuro")) {
    storage.set("modoOscuro", false);
  }

  const [modoOscuro] = useState(
    storage.get<boolean>("modoOscuro") ?? false
  );

  return (
    <main
      className={
        (modoOscuro ? "dark" : "") +
        (location.pathname === "/" || location.pathname === "/crear"
          ? " login"
          : "")
      }
    >
      {children}
    </main>
  );
}

export default Main;