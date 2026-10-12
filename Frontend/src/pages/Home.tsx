import NavBar from "../components/Navbar"
import Header from "../components/Header"

import Main from "../components/Main";
function Home() {

 
  return (
    <Main>
      
     <Header/>

      <section >
     <div className="listabloques">
      <div className="listacentro">
        <img src="proceso.svg" className="proceso" style={{width:"12vh"}} alt="" />
        <h3>En proceso</h3>
      </div>
     </div>
   
      </section>

     <NavBar/>
   </Main>
  );
}

export default Home