import './App.css'
import Schedule from './components/Schedule'

function App({ base_url, username, prid, csid }: { base_url: string, username: string | null, prid: string | null, csid: string | null }) {
 console.log("csid: ", csid);
  return (
    <>
     <Schedule base_url={base_url} username_={username} prid={prid} csid={csid} />
    </>
  )
}

export default App
