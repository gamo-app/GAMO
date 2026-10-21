import { Outlet } from "react-router-dom";
import Header from "./Header";
import NavBar from "./Navbar";
import Main from "./Main";

function Layout() {
  return (
    <Main>
      <Header />
      <Outlet />
      <NavBar />
    </Main>
  );
}

export default Layout;