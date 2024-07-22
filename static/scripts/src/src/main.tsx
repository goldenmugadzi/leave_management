import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'// Get the current page's pathname

const path: string = window.location.pathname;

// Determine the element ID based on the current page
let elementId;
switch (true) {
  case path.includes('comperative_schedule'):
    elementId = 'create_comparative_schedule';
    break;
  case path === '/about':
    elementId = 'aboutRoot';
    break;
  // Add more cases as needed for different pages
  default:
    elementId = 'root'; // Fallback to a default element
}

// Safely attempt to select the element and use it
const element = document.getElementById(elementId);
let BASE_URL: string = '';
let url: string | null = '';
let username: string| null = '';
let prid: string| null = '';
let csid: string| null = '';
if (element) {
    console.log("element: ", element);
  // For example, you might want to render a React component into this element
    url = element.getAttribute("data-baseurl");
    BASE_URL = url+'/comperative_schedule';
    username = element.getAttribute("data-username");
    prid = element.getAttribute("data-prid");
    csid = element.getAttribute("data-csid");
  // Perform operations with the element
  // For example, you might want to render a React component into this element
} else {
  console.error(`Element with ID '${elementId}' not found.`);
}

ReactDOM.createRoot(element!).render(
  <React.StrictMode>
    <App base_url={BASE_URL} username={username} prid={prid} csid={csid} />
  </React.StrictMode>,
)
