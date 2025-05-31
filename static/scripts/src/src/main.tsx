import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import DSM from './pages/dsm_dashbaords/Dsm.tsx'
import './index.css'// Get the current page's pathname

let dsm_dashboard_element: HTMLElement | null = null;
try {
    dsm_dashboard_element = document.getElementById('dsm_dashboards_id');
    if (dsm_dashboard_element) {
       const username = dsm_dashboard_element.getAttribute("data-username");
       const user_role = dsm_dashboard_element.getAttribute("data-user_role");
       const url = dsm_dashboard_element.getAttribute("data-baseurl")?? null;
       const BASE_URL = url;
       ReactDOM.createRoot(dsm_dashboard_element!).render(
        <React.StrictMode>
          <DSM base_url={BASE_URL ?? ''} username={username ?? ''} user_role={user_role ?? ''} />
        </React.StrictMode>,
      )
    } else {
      console.error("dsm_dashboard_element not found");
    }
} catch (error) {
    console.error("Error getting dsm_dashboard_element: ", error);
}

try {
  
  const elementId = 'create_comparative_schedule';
  const element = document.getElementById(elementId);

  if(element){
    const path: string = window.location.pathname;
    console.log("path: ", path);

    // Determine the element ID based on the current page
    let BASE_URL: string = '';
    let url: string | null = '';
    switch (true) {
        case path.includes('/direct_purchase/'):
            url = element?.getAttribute("data-baseurl")?? null;
            BASE_URL = url+'/direct_purchase';
            break;
        case path.includes('/restricted_bidding/'):
                url = element?.getAttribute("data-baseurl")?? null;
                BASE_URL = url+'/restricted_bidding';
                break;
        case path.includes('/comperative_schedule/'):
            url = element?.getAttribute("data-baseurl")?? null;
            BASE_URL = url+'/comperative_schedule';
            break;
        // Add more cases as needed for different pages
        default:
            console.error("No matching path found");
            break;
    }

    // Safely attempt to select the element and use it
    let username: string| null = '';
    let prid: string| null = '';
    let csid: string| null = '';
    if (element) {
        console.log("element: ", element);
      // For example, you might want to render a React component into this element
        username = element.getAttribute("data-username");
        prid = element.getAttribute("data-prid");
        csid = element.getAttribute("data-csid");
      // Perform operations with the element
      // For example, you might want to render a React component into this element
    } else {
      console.error(`Element with ID '${elementId}' not found.`);
    }

    console.log("BASE_URL: ", BASE_URL);

    ReactDOM.createRoot(element!).render(
      <React.StrictMode>
        <App base_url={BASE_URL} username={username} prid={prid} csid={csid} />
      </React.StrictMode>,
    )
  } else {
    console.error(`Element with ID '${elementId}' not found.`);
  }

} catch (error) {
    console.error("Error getting dsm_dashboard_element: ", error);
}