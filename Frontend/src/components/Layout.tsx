import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import Header from "./Header";
import NavBar from "./Navbar";
import Main from "./Main";
import Presentacion from "./Presentacion";

function Layout() {
  const { pathname } = useLocation();
  const [mostrarPresentacion, setMostrarPresentacion] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMostrarPresentacion(false);
    }, 2500);

    return () => window.clearTimeout(timer);
  }, []);

  const rutasLogin = ["/", "/crear"];
const rutasAtras = [
  "/escanear",
  "/notificacion",
  "/contraseña",
  "/agregarsocio",
];

  const rutasSinNavBar = [
    "/",
    "/crear",
    "/escanear",
    "/contraseña",
    "/agregarsocio",

  ];

  const rutasSalir = ["/contraseña"];

  const login = rutasLogin.includes(pathname);

const atras =
  rutasAtras.includes(pathname) ||
  pathname.startsWith("/registrar/") ||
  /^\/socios\/[^/]+$/.test(pathname) ||
  /^\/gestion\/[^/]+$/.test(pathname) ||
  /^\/escanear\/[^/]+$/.test(pathname) ||
  /^\/agregar\/[^/]+$/.test(pathname);

const salir = rutasSalir.includes(pathname);

const mostrarNavBar =
  !rutasSinNavBar.includes(pathname) &&
  !pathname.startsWith("/escanear/");

  return (
    <>
      {mostrarPresentacion && <Presentacion />}

      <Main>
        <Header login={login} atras={atras} salir={salir} />

        <Outlet />

        {mostrarNavBar && <NavBar />}
      </Main>

    </>
  );
}

export default Layout;