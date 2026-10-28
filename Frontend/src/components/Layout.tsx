import { Outlet, useLocation } from "react-router-dom";

import Header from "./Header";
import NavBar from "./Navbar";
import Main from "./Main";

function Layout() {
  const { pathname } = useLocation();

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
 const rutasSalir = [
    "/contraseña",
  ];

  const login = rutasLogin.includes(pathname);

  const atras =
    rutasAtras.includes(pathname) ||
    /^\/socios\/[^/]+$/.test(pathname) ||
    /^\/gestion\/[^/]+$/.test(pathname) ||
    /^\/agregar\/[^/]+$/.test(pathname);

  const salir =  rutasSalir.includes(pathname)

  const mostrarNavBar = !rutasSinNavBar.includes(pathname);

  return (
    <Main>
      <Header login={login} atras={atras} salir={salir} />

      <Outlet />

      {mostrarNavBar && <NavBar />}
    </Main>
  );
}

export default Layout;