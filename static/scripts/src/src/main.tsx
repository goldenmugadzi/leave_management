import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'// Get the current page's pathname

const path: string = window.location.pathname;
console.log("path: ", path);

// Determine the element ID based on the current page
let elementId;
let BASE_URL: string = '';
let url: string | null = '';
let element: HTMLElement | null = null;
switch (true) {
    case path.includes('/direct_purchase/'):
        elementId = 'create_comparative_schedule';
        element = document.getElementById(elementId);
        url = element?.getAttribute("data-baseurl")?? null;
        BASE_URL = url+'/direct_purchase';
        break;
    case path.includes('/restricted_bidding/'):
            elementId = 'create_comparative_schedule';
            element = document.getElementById(elementId);
            url = element?.getAttribute("data-baseurl")?? null;
            BASE_URL = url+'/restricted_bidding';
            break;
    case path.includes('/comperative_schedule/'):
        elementId = 'create_comparative_schedule';
        element = document.getElementById(elementId);
        url = element?.getAttribute("data-baseurl")?? null;
        BASE_URL = url+'/comperative_schedule';
        break;
    // Add more cases as needed for different pages
    default:
        elementId = 'root'; // Fallback to a default element
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
