import NavBar from "../components/Navbar"
import Header from "../components/Header"
import Main from "../components/Main";
function Buscar() {

  return (
    <Main>
      
     <Header/>

      <section>
     <div className="listabloques">
      <div className="bloque">
        <input type="text" className="blanco" />
      </div>

     </div>
   
      </section>

     <NavBar/>
   </Main>
  );
}

export default Buscar