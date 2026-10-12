import ListaHorarios from "../components/ListaHorarios"
import NavBar from "../components/Navbar"
import Header from "../components/Header"
import Main from "../components/Main";

function Clases() {

  const horarios = [
    { estado: 0, fecha: "2026-10-06T10:00:00", deporte:"Voley" },
    { estado: 1, fecha: "2026-10-06T09:00:00", deporte:"Muay thai" },
    { estado: 2, fecha: "2026-10-06T08:00:00", deporte:"Yoga" },
    { estado: 3, fecha: "2026-10-07T10:00:00", deporte:"Yoga" },
    { estado: 0, fecha: "2026-10-07T09:00:00", deporte:"Muay thai" },
  ];
  return (
    <Main>
      
     <Header/>

      <section>
     <div className="listabloques">
      <ListaHorarios horarios={horarios} />

     </div>
   
      </section>

     <NavBar/>
   </Main>
  );
}

export default Clases