<?php
session_start();
require_once('../connection.php');
require_once('../user_profile.php');
error_reporting(0);
$section_code = $_SESSION['section_code'];
$roles = $_SESSION['roles'];
$role = $_SESSION['role'];
$role1 = $_SESSION['role1'];
$role2 = $_SESSION['role2'];
$role3 = $_SESSION['role3'];
$role4 = $_SESSION['role4'];
$role5 = $_SESSION['role5'];
$role6 = $_SESSION['role6'];
$role7 = $_SESSION['role7'];
$role8 = $_SESSION['role8'];
$role9 = $_SESSION['role9'];
$region = $_SESSION['region'];
$district = $_SESSION['district'];
$username = $_SESSION['username'];
$pass = $_SESSION['password'];

$sql = mysqli_query($con, "SELECT type FROM users.centres WHERE centre_code='$section_code'");
$count = mysqli_num_rows($sql);
if ($count > 0) {
    while ($row = mysqli_fetch_array($sql)) {
        $type = $row['type'];
    }
} else {
    $type = '';
}

?>
<!doctype html>
<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Excellence</title>
    <link rel="shortcut icon" href="../../assets/imgs/website-logo.png" />
    <link href="../../assets/css/tailwind.css" rel="stylesheet">
    <link href="../../assets/css/be.css" rel="stylesheet">
</head>

<body>
<main style="height: 100%; display: flex;" class="bg-gray-100">
    <div style="flex: 1;">
        <nav class="bg-blue-925">
            <div class="mx-auto px-2 sm:px-6 md:px-2 lg:px-2 xl:px-2">
                <div class="relative flex h-16 items-center justify-between">
                    <div class="absolute inset-y-0 left-0 flex items-center sm:hidden">
                        <!-- Mobile menu button-->
                        <button type="button"
                                class="relative inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-blue-550 hover:text-white focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                                aria-controls="mobile-menu" aria-expanded="false">
                            <span class="absolute -inset-0.5"></span>
                            <span class="sr-only">Open main menu</span>
                            <!--
        Icon when menu is closed.

        Menu open: "hidden", Menu closed: "block"
      -->
                            <svg class="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                                 stroke="currentColor" aria-hidden="true">
                                <path stroke-linecap="round" stroke-linejoin="round"
                                      d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                            </svg>
                            <!--
        Icon when menu is open.

        Menu open: "block", Menu closed: "hidden"
      -->
                            <svg class="hidden h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                                 stroke="currentColor" aria-hidden="true">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div
                        class="flex flex-1 items-center sm:items-stretch sm:justify-between md:justify-between lg:justify-between xl:justify-between">
                        <div class="flex flex-shrink-0 items-center">
                            <img class="h-14 w-auto" src="../../assets/imgs/zetdc.png" alt="ZETDC">
                        </div>
                        <div class="flex sm:ml-6 items-center">
                            <div class="">
                                <!-- Current: "bg-gray-900 text-white", Default: "text-gray-300 hover:bg-blue-550 hover:text-white" -->
                                <a href="#" class="text-wht rounded-md px-3 py-2 font-medium" aria-current="page">
                                    <span>ZETDC BUSINESS EXCELLENCE</span>
                                </a>
                            </div>
                        </div>
                    </div>
                    <div
                        class="absolute hide inset-y-0 right-0 flex items-center pr-2 sm:static sm:inset-auto sm:ml-6 sm:pr-0">
                        <div class="relative" x-data="{ open: false }">
                            <div>
                                <button @click="open = ! open" type="button"
                                        class="relative ml-3 flex items-center text-blue-50 p-2 hover:bg-blue-550 rounded focus:outline-none focus:ring-2 focus:ring-tory-blue-50 focus:ring-offset-2 focus:ring-offset-gray-800 px-2 py-1"
                                        id="user-menu-button" aria-expanded="false" aria-haspopup="true">
                                    <span class="absolute -inset-1.5"></span>
                                    <span class="sr-only">ACCOUNT</span>
                                    <span
                                        class="text-tory-blue-50"><?php displayLoggedUser($username, $pass); ?></span>
                                    <span class="ml-2">
                                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                                 stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                                                <path stroke-linecap="round" stroke-linejoin="round"
                                                      d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                                            </svg>
                                        </span>
                                </button>
                            </div>

                            <!--
                        Dropdown menu, show/hide based on menu state.

                        Entering: "transition ease-out duration-100"
                        From: "transform opacity-0 scale-95"
                        To: "transform opacity-100 scale-100"
                        Leaving: "transition ease-in duration-75"
                        From: "transform opacity-100 scale-100"
                        To: "transform opacity-0 scale-95"
                    -->
                            <div x-show="open" @click.outside="open = false" class="text-black absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none
                            " role="menu" aria-orientation="vertical" aria-labelledby="user-menu-button" tabindex="-1">
                                <!-- Active: "bg-gray-100", Not Active: "" -->
                                <a href="../../comments/forms.php"
                                   class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-550 rounded m-1 hover:text-blue-50"
                                   role="menuitem" tabindex="-1" id="user-menu-item-3">FEEDBACK</a>
                                <a href="../editmydetails.php"
                                   class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-550 rounded m-1 hover:text-blue-50"
                                   role="menuitem" tabindex="-1" id="user-menu-item-1">CHANGE PASSWORD</a>
                                <a href="../logout.php"
                                   class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-550 rounded m-1 hover:text-blue-50"
                                   role="menuitem" tabindex="-1" id="user-menu-item-2">LOGOUT</a>
                            </div>
                        </div>

                        <button type="button"
                                class="relative ml-3 rounded p-2 text-blue-50 hover:bg-blue-550 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800">
                            <a href="../../comments/forms.php">
                                <span class="absolute -inset-1.5"></span>
                                <span class="sr-only">FEEDBACK</span>
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                     stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                                    <path stroke-linecap="round" stroke-linejoin="round"
                                          d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.068.157 2.148.279 3.238.364.466.037.893.281 1.153.671L12 21l2.652-3.978c.26-.39.687-.634 1.153-.67 1.09-.086 2.17-.208 3.238-.365 1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                                </svg>
                            </a>
                        </button>

                        <button type="button"
                                class="relative ml-3 rounded p-2 hover:bg-blue-550 text-blue-50 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800">
                            <a href="../logout.php">
                                <span class="absolute -inset-1.5"></span>
                                <span class="sr-only">LOGOUT</span>

                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                     stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                                    <path stroke-linecap="round" stroke-linejoin="round"
                                          d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
                                </svg>
                            </a>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Mobile menu, show/hide based on menu state. -->
            <!-- <div class="sm:hidden" id="mobile-menu">
        <div class="space-y-1 px-2 pb-3 pt-2">
            <a href="#" class="text-white block rounded-md px-3 py-2 text-base font-medium"
                aria-current="page">Dashboard</a>
            <a href="#"
                class="text-gray-300 hover:bg-blue-550 hover:text-white block rounded-md px-3 py-2 text-base font-medium">Team</a>
            <a href="#"
                class="text-gray-300 hover:bg-blue-550 hover:text-white block rounded-md px-3 py-2 text-base font-medium">Projects</a>
            <a href="#"
                class="text-gray-300 hover:bg-blue-550 hover:text-white block rounded-md px-3 py-2 text-base font-medium">Calendar</a>
        </div>
    </div> -->
        </nav>

        <div class="flex">
            <div id="sidebar" style="width: 15%;" class="bg-blue-925">
                <aside>
                    <!-- Component Start -->
                    <div style="display: flex; flex-direction: column;" class="text-gray-50 rounded mt-3">
                        <a style="margin-top: 3rem;" class="flex items-center w-full px-3" href="#">
                            <svg class="w-8 h-8 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"
                                 fill="currentColor">
                                <path
                                    d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z" />
                            </svg>
                            <span class="item-center ml-2 text-sm font-bold">BUSINESS EXCELLENCE</span>
                        </a>
                        <div class="w-full px-2">
                            <div style="display: flex; flex-direction: column;"
                                 class="text-gray-50 w-full mt-3 border-t border-gray-700">
                                <a class="flex items-center w-full h-12 px-3 mt-2 rounded hover:bg-blue-550"
                                   href="../main1.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Home</span>
                                </a>
                                <a class="flex items-center w-full h-12 px-3 mt-2 rounded hover:bg-blue-550"
                                   href="../second_menu/business_application.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round"
                                              d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Business Applications</span>
                                </a>
                                <a class="flex items-center w-full h-12 px-3 mt-2 hover:bg-blue-550 rounded"
                                   href="../second_menu/Trending Bulletings.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Trending Bulletings</span>
                                </a>
                                <a class="flex items-center w-full h-12 px-3 mt-2 rounded hover:bg-blue-550"
                                   href="../second_menu/knowledge_centre.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Knowledge Centre</span>
                                </a>
                            </div>
                            <div style="display: flex; flex-direction: column;"
                                 class="text-gray-50 w-full mt-2 border-t border-gray-700">
                                <a class="flex items-center w-full h-12 px-3 mt-2 rounded hover:bg-blue-550"
                                   href="../second_menu/strategic_objectives.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Strategic Objectives</span>
                                </a>
                                <a class="flex items-center w-full h-12 px-3 mt-2 rounded hover:bg-blue-550"
                                   href="../second_menu/processes_procedures.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Processes and Procedures</span>
                                </a>
                                <a class="flex items-center w-full h-12 px-3 mt-2 rounded hover:bg-blue-550"
                                   href="../second_menu/competence_building.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Competence Building</span>
                                    <span
                                        class="absolute top-0 left-0 w-2 h-2 mt-2 ml-2 bg-indigo-500 rounded-full"></span>
                                </a>
                                <a class="flex items-center w-full h-12 px-3 mt-2 rounded hover:bg-blue-550"
                                   href="../second_menu/engagement_forums.php">
                                    <svg class="w-6 h-6 stroke-current" xmlns="http://www.w3.org/2000/svg"
                                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                                    </svg>
                                    <span class="ml-2 text-sm font-medium">Engagement Forums</span>
                                    <span
                                        class="absolute top-0 left-0 w-2 h-2 mt-2 ml-2 bg-indigo-500 rounded-full"></span>
                                </a>
                            </div>
                        </div>
                    </div>
                    <!-- Component End  -->
                </aside>
            </div>
            <div id="content" style="width: 85%;" class="bg-gray-100">

                <header class="">
                    <div class="mx-auto px-4 py-6 sm:px-6 md:px-4 lg:px-8 xl:px-4">
                        <h1 class="text-3xl font-bold tracking-tight text-nepal-950">
                            BUSINESS APPLICATIONS
                        </h1>
                    </div>
                </header>
                <div style="margin-bottom: 10rem;" class="mx-auto px-4 py-6 sm:px-6 lg:px-8">
                    <!-- COMMERCIAL START -->
                    <div class="grid grid-cols-3 gap-4">
                        <div class="w-auto bg-gray-200 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
                            <div class="sm:flex lg:items-center lg:justify-between">
                                <div class="min-w-0 flex-1">
                                    <div class="">
                                        <div class="mx-auto">

                                            <div class="group relative">
                                                <div
                                                    class="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-md bg-gray-200 lg:aspect-none group-hover:opacity-75 lg:h-40">
                                                    <img src="../../assets/imgs/electrical.jpg" alt=""
                                                         class="h-full w-full object-cover object-center lg:h-full lg:w-full">
                                                </div>
                                                <div class="mt-4 flex justify-center">
                                                    <div class="w-full">
                                                        <div
                                                            class="dropdown-group inline-block w-full text-blue-50">
                                                            <button
                                                                class="w-full bg-blue-800 hover:bg-blue-900 outline-none focus:outline-none border px-3 py-1 rounded flex items-center">
                                                                    <span
                                                                        class="pr-1 font-semibold flex-1 text-blue-50">COMMERCIAL</span>
                                                                <span class="text-blue-50">
                                                                        <svg class="fill-current h-4 w-4 transform group-hover:-rotate-180
                                                                                transition duration-150 ease-in-out"
                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                             viewBox="0 0 20 20">
                                                                            <path
                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                        </svg>
                                                                    </span>
                                                            </button>


                                                            <ul style="min-width: 18rem;"
                                                                class="bg-blue-50 z-10 text-gray-950 border rounded transform scale-0 group-hover:scale-100 absolute
                                                                            transition duration-150 ease-in-out origin-top">

                                                                <li
                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a tabindex="-1"
                                                                       href="http://172.16.8.97:8200/commercials/connections/all-connections">
                                                                        Connections
                                                                    </a>
                                                                </li>
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                        <span class="pr-1 flex-1">Tokens</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                        transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                min-w-32 text-gray-950
                                                                                ">

                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span class="pr-1 flex-1">Clear
                                                                                        Credit Request</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                <?php
                                                                                if ($role3 == "create" || $role3 == "CS" || $role3 == "CG") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tokens/credit_request.php">
                                                                                            CREATE
                                                                                        </a>
                                                                                    </li>
                                                                                <?php } else {
                                                                                } ?>
                                                                                <li
                                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                    <button
                                                                                        class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                            <span
                                                                                                class="pr-1 flex-1">VIEW</span>
                                                                                        <span class="mr-auto">
                                                                                                <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                                     viewBox="0 0 20 20">
                                                                                                    <path
                                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                                </svg>
                                                                                            </span>
                                                                                    </button>

                                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                        <?php if ($role3 == "approve") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/section/pending_sectionhead.php">Pending
                                                                                                    Approval</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/section/reports.php">Reports</a>
                                                                                            </li>

                                                                                        <?php } else if ($role3 == "create" || $role3 == "CS") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/user/pending_sectionhead.php">Pending
                                                                                                    Approval</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/user/pending_closure.php">Pending
                                                                                                    Closure</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/user/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "generation") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/finance/pending_finance.php">Pending
                                                                                                    Generation</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/finance/reports.php">Reports</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/finance/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "CG") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/finance/pending_finance.php">Pending
                                                                                                    Generation</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/finance/reports_CG.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "audit") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/user/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else {
                                                                                        } ?>
                                                                                    </ul>
                                                                                </li>
                                                                            </ul>
                                                                        </li>
                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span class="pr-1 flex-1">Tamper
                                                                                        Token Request</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                <?php if ($role3 == "create" || $role3 == "CS" || $role3 == "CG") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a tabindex="-1"
                                                                                           href="../../tokens/tamper_token/tamper_token.php">CREATE</a>
                                                                                    </li>
                                                                                <?php } else {
                                                                                } ?>
                                                                                <li
                                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                    <button
                                                                                        class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                            <span
                                                                                                class="pr-1 flex-1">VIEW</span>
                                                                                        <span class="mr-auto">
                                                                                                <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                                     viewBox="0 0 20 20">
                                                                                                    <path
                                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                                </svg>
                                                                                            </span>
                                                                                    </button>

                                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                        <?php if ($role3 == "approve") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/section/pending_sectionhead.php">Pending
                                                                                                    Approval</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/section/reports.php">Reports</a>
                                                                                            </li>

                                                                                        <?php } else if ($role3 == "create" || $role3 == "CS") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/user/pending_sectionhead.php">Pending
                                                                                                    Approval</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/user/pending_closure.php">Pending
                                                                                                    Closure</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/user/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "generation") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/finance/pending_finance.php">Pending
                                                                                                    Generation</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/finance/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "CG") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/finance/pending_finance.php">Pending
                                                                                                    Generation</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/finance/reports_CG.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "audit") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/user/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else {
                                                                                        } ?>
                                                                                    </ul>
                                                                                </li>
                                                                            </ul>
                                                                        </li>

                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span
                                                                                        class="pr-1 flex-1">Reimbursement
                                                                                        Token Request</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                <?php if ($role3 == "create" || $role3 == "CS" || $role3 == "CG") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a tabindex="-1"
                                                                                           href="../../tokens/reimbursement_token/reimbursement_token.php">CREATE</a>
                                                                                    </li>
                                                                                <?php } else {
                                                                                } ?>
                                                                                <li
                                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                    <button
                                                                                        class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                            <span
                                                                                                class="pr-1 flex-1">VIEW</span>
                                                                                        <span class="mr-auto">
                                                                                                <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                                     viewBox="0 0 20 20">
                                                                                                    <path
                                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                                </svg>
                                                                                            </span>
                                                                                    </button>

                                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                        <?php if ($role3 == "approve") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/section/pending_sectionhead.php">Pending
                                                                                                    Approval</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/section/reports.php">Reports</a>
                                                                                            </li>

                                                                                        <?php }
                                                                                        if ($role3 == "meter downloading") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/engineer/pending_engineer.php">Download
                                                                                                    Meter</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/engineer/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "create") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/user/pending_sectionhead.php">Pending
                                                                                                    Approval</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/user/pending_closure.php">Pending
                                                                                                    Closure</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                Closure</a>
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/user/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "stores") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                Closure</a>
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/stores/pending_stores.php">Pending
                                                                                                    Loading</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                Closure</a>
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/stores/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "generation") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/finance/pending_finance.php">Pending
                                                                                                    Generation</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/finance/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "CS") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/stores/pending_stores.php">Pending
                                                                                                    Loading</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/user/pending_sectionhead.php">Pending
                                                                                                    Approval</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/user/pending_closure.php">Pending
                                                                                                    Closure</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/stores/reports_CS.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "CG") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/finance/pending_finance.php">Pending
                                                                                                    Generation</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/reimbursement_token/finance/reports_CG.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else if ($role3 == "audit") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a tabindex="-1"
                                                                                                   href="../../tokens/tamper_token/user/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else {
                                                                                        } ?>
                                                                                    </ul>
                                                                                </li>
                                                                            </ul>
                                                                        </li>
                                                                    </ul>
                                                                </li>
                                                            </ul>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- More products... -->
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>

                        <!-- COMMERCIAL END -->
                        <!-- FINANCE START -->

                        <div class="w-auto bg-gray-200 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
                            <div class="sm:flex lg:items-center lg:justify-between">
                                <div class="min-w-0 flex-1">
                                    <div class="">
                                        <div class="mx-auto">

                                            <div class="group relative">
                                                <div
                                                    class="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-md bg-gray-200 lg:aspect-none group-hover:opacity-75 lg:h-40">
                                                    <img src="../../assets/imgs/electrical.jpg" alt=""
                                                         class="h-full w-full object-cover object-center lg:h-full lg:w-full">
                                                </div>
                                                <div class="mt-4 flex justify-center">
                                                    <div class="w-full ">
                                                        <div
                                                            class="dropdown-group inline-block w-full text-blue-50">
                                                            <button
                                                                class="w-full bg-blue-800 hover:bg-blue-900 outline-none focus:outline-none border px-3 py-1 rounded flex items-center">
                                                                    <span
                                                                        class="pr-1 font-semibold flex-1 text-blue-50">FINANCE</span>
                                                                <span class="text-blue-50">
                                                                        <svg class="fill-current h-4 w-4 transform group-hover:-rotate-180
                                                                                transition duration-150 ease-in-out"
                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                             viewBox="0 0 20 20">
                                                                            <path
                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                        </svg>
                                                                    </span>
                                                            </button>

                                                            <ul style="min-width: 18rem;"
                                                                class="bg-blue-50 z-10 text-gray-950 border rounded transform scale-0 group-hover:scale-100 absolute
                                                                            transition duration-150 ease-in-out origin-top">

                                                                <!-- ACE START -->
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                        <span class="pr-1 flex-1">ACE</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                        transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                min-w-32 text-gray-950
                                                                                ">
                                                                        <?php if ($role5 == "create") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a href="../../../ace/ace.php">
                                                                                    CREATE ACE
                                                                                </a>
                                                                            </li>
                                                                            <?php
                                                                        } elseif ($role5 == "process") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../ace/accounting/virament.php">
                                                                                    VIRARAMENT
                                                                                </a>
                                                                            </li>
                                                                        <?php } elseif ($role5 == "sanction") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../ace/finance/finance_virament.php">
                                                                                    VIRARAMENT
                                                                                </a>
                                                                            </li>
                                                                        <?php } else {
                                                                        } ?>
                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span class="pr-1 flex-1">VIEW
                                                                                        ACEs</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                <?php if ($role5 == "check") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/depot/pending_cso.php">Pending
                                                                                            Checking</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } else if ($role5 == "create") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } else {
                                                                                }

                                                                                ?>
                                                                                <?php
                                                                                if ($role5 == "pass") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/pending_sectionhead.php">Awaiting
                                                                                            Pass</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/pending_virament.php">Virament
                                                                                            Requests</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } else if ($role5 == "audit") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php  }


                                                                                //innerif termination
                                                                                else if ($role5 == "create") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/user/pending_sectionhead.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } //else if termination
                                                                                elseif ($role5 == "process") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/accounting/pending_accounts.php">Awaiting
                                                                                            Update</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/accounting/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } //2nnd inner elseif end UPTO HERE
                                                                                elseif ($type == "district" && $role5 == "create") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/user/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif ($type == "district" && $role5 == "pass") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/pending_sectionhead.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/pending_virament.php">Virament
                                                                                            Requests</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/network_manager.php">Reports</a>
                                                                                    </li>
                                                                                <?php } else if ($role5 == "sanction") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/pending_sectionhead.php">Awaiting
                                                                                            Pass</a>
                                                                                        < </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/finance/pending_finance.php">Awaiting
                                                                                            Sanctioning</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/finance/pending_virament.php">Pending
                                                                                            Virament</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/finance/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } else if ($role5 == "order") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/procurement/pending_order.php">Pending
                                                                                            Order</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/procurement/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } elseif ($role5 == "approve") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/section/pending_sectionhead.php">Awaiting
                                                                                            Pass</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/gm/pending_gm.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/gm/pending_virament.php">Pending
                                                                                            Virament</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../ace/gm/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } else {
                                                                                }
                                                                                ?>
                                                                            </ul>
                                                                        </li>

                                                                    </ul>
                                                                </li>
                                                                <!-- ACE END -->

                                                                <!-- PB START -->
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span class="pr-1 flex-1">PURCHASE BELOW
                                                                                LIMIT</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                        transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                min-w-32 text-gray-950
                                                                                ">
                                                                        <?php if ($role5 == "create") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a href="../../../ace/ace.php">
                                                                                    CREATE ACE
                                                                                </a>
                                                                            </li>
                                                                            <?php
                                                                        } elseif ($role5 == "process") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../ace/accounting/virament.php">
                                                                                    VIRARAMENT
                                                                                </a>
                                                                            </li>
                                                                        <?php } elseif ($role5 == "sanction") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../ace/finance/finance_virament.php">
                                                                                    VIRARAMENT
                                                                                </a>
                                                                            </li>
                                                                        <?php } else {
                                                                        }
                                                                        ?>
                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span class="pr-1 flex-1">VIEW
                                                                                        ACEs</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                            transition duration-150 ease-in-out origin-top-left
                                                                                            min-w-32 text-gray-950
                                                                                            ">
                                                                                <li
                                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                    REPORTS</li>
                                                                            </ul>
                                                                        </li>

                                                                    </ul>
                                                                </li>
                                                                <!-- PB END -->

                                                                <!-- DIRECT PURCHASE START -->
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span class="pr-1 flex-1">DIRECT
                                                                                PURCHASE</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                        transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                min-w-32 text-gray-950
                                                                                ">
                                                                        <?php
                                                                        if ($role2 == "create" || $role2 == "CA" || $role2 == "CC" || $role2 == "CAC") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../direct_purchases/adjudication.php">Create</a>
                                                                            </li>
                                                                            <?php
                                                                        }
                                                                        else
                                                                        {?>
                                                                        <li
                                                                            class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <a
                                                                                href="../../direct_purchases/adjudication.php">Create</a>
                                                                        </li>



                                                                        }
                                                                        ?>

                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span
                                                                                        class="pr-1 flex-1">VIEW</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                            transition duration-150 ease-in-out origin-top-left
                                                                                            min-w-32 text-gray-950
                                                                                            ">
                                                                                <li
                                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                    <a
                                                                                        href="../../direct_purchases/depot/reports.php">Reports</a>
                                                                                </li>
                                                                                <?php


                                                                                //if ($type == "depot") { //outer if
                                                                                if ("depot" == "depot") {
                                                                                    if ($role2 == "create") {
                                                                                        ?>
                                                                                        <?php if ($role5 == "create") { ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a
                                                                                                    href="../../direct_purchases/depot/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } //innerif termination
                                                                                        else if ($role2 == "check") {
                                                                                            ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a
                                                                                                    href="../../direct_purchases/depot/check_adjudication.php">Pending
                                                                                                    Verification</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a
                                                                                                    href="../../direct_purchases/depot/reports.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } //innerif termination
                                                                                        else if ($role2 == "CC") {
                                                                                            ?>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a
                                                                                                    href="../../direct_purchases/depot/check_adjudication.php">Pending
                                                                                                    Verification</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a
                                                                                                    href="../../direct_purchases/depot/reports_CC.php">Reports</a>
                                                                                            </li>
                                                                                        <?php } else {
                                                                                        }
                                                                                    }
                                                                                }
                                                                                ?>
                                                                                <?php
                                                                                if ($type == "section" && $role2 == "create") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/user/pending_sectionhead.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } //innerif termination
                                                                                else if ($type == "section" && $role2 == "CA") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/section_head/pending_sectionhead.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/section_head/reports_CA.php">Reports</a>
                                                                                    </li>

                                                                                    <?php
                                                                                } //else if termination
                                                                                else if ($type == "section" && $role2 == "process") {
                                                                                    ?>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/procurement/pending_procurement.php">Pending
                                                                                            Checking</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/procurement/pending_order.php">Pending
                                                                                            Order Number</a>
                                                                                    </li>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/procurement/reports.php">Reports</a>
                                                                                    </li>

                                                                                <?php } //2nnd inner elseif end
                                                                                else if ($role2 == "approve" && $type == "section") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/section_head/pending_sectionhead.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/section_head/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif ($type == "district" && $role2 == "audit") { ?>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/section_head/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif ($type == "district" && $role2 == "CA") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/district/pending_nm.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/district/reports_CA.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif ($type == "district" && $role2 == "approve") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/finance/pending_finance.php">Pending
                                                                                            Confirmation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/finance/reports.php">Report</a>
                                                                                    </li>
                                                                                <?php } else if ($role2 == "confirm") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/finance/pending_finance.php">Pending
                                                                                            Confirmation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/finance/reports.php">Report</a>
                                                                                    </li>
                                                                                <?php } elseif ($role2 == "authorise") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/gm/pending_gm.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/section_head/pending_sectionhead.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/gm/reports.php">Regional
                                                                                            Reports</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../direct_purchases/section_head/reports.php">Section
                                                                                            Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } else {
                                                                                } ?>

                                                                            </ul>

                                                                        </li>

                                                                    </ul>
                                                                </li>
                                                                <!-- DIRECT PURCHASE END -->

                                                                <!-- PURCHASE ABOVE START -->
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span class="pr-1 flex-1">PURCHASE ABOVE
                                                                                LIMIT</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                        transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                min-w-32 text-gray-950
                                                                                ">

                                                                        <?php if ($role4 == "create") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/supplier.php">Create</a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/rfq/datatables/production/procurement_processed.php">Create
                                                                                    (from RFQ)</a>
                                                                            </li>
                                                                            <?php
                                                                        } elseif ($role4 == "check") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/finance/pending_finance.php">Pending
                                                                                    Checking</a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/rfq/datatables/production/awaiting_authorisation.php">RFQ`s
                                                                                    Pending Authorisation</a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/committee/pending_committee.php">Pending
                                                                                    Committee</a>
                                                                            </li>
                                                                            <?php
                                                                        } elseif ($role4 == "approve") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a href="../../tender/gm/pending.php">Pending
                                                                                    Approval</a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/gm/reports.php">Reports</a>
                                                                            </li>
                                                                            <?php
                                                                        } elseif ($role4 == "approve") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a href="../../tender/gm/pending.php">Pending
                                                                                    Approval</a>
                                                                            </li>

                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/gm/reports.php">Reports</a>
                                                                            </li>
                                                                            <?php //RFQ application roles
                                                                        } elseif ($role4 == "request") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/rfq/user/make_request.php">Request
                                                                                    for
                                                                                    Quotation</a>
                                                                            </li>
                                                                            <?php
                                                                        } elseif ($role4 == "authorise") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/rfq/datatables/production/awaiting_authorisation.php">Pending
                                                                                    Authorisation</a>
                                                                            </li>
                                                                            <?php
                                                                        } elseif ($role4 == "verify") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../tender/rfq/datatables/production/awaiting_verification.php">Pending
                                                                                    Verification</a>
                                                                            </li> <?php
                                                                        } else {
                                                                        } ?>


                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span
                                                                                        class="pr-1 flex-1">VIEW</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                    transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>

                                                                            <?php if ($role4 == "create") { ?>
                                                                                <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                            transition duration-150 ease-in-out origin-top-left
                                                                                            min-w-32 text-gray-950
                                                                                            ">
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/rfq/datatables/production/awaiting_authorisation.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/rfq/datatables/production/awaiting_procurement.php">Pending
                                                                                            Procurement</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/pending_approval.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/committee/pending_committee.php">Pending
                                                                                            Committee</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/pending_order.php">Pending
                                                                                            Order</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/reports.php">Reports</a>
                                                                                    </li>
                                                                                </ul>
                                                                                <?php
                                                                            } elseif ($role4 == "audit") { ?>
                                                                                <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                        transition duration-150 ease-in-out origin-top-left
                                                                                        min-w-32 text-gray-950
                                                                                        ">

                                                                                <li
                                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                    <a
                                                                                        href="../../tender/reports.php">Reports</a>
                                                                                </li>
                                                                            <?php } elseif ($role4 == "check") { ?>
                                                                                <li
                                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                    <a
                                                                                        href="../../tender/finance/reports.php">Reports</a>
                                                                                </li>
                                                                                </ul>
                                                                                <?php
                                                                            } elseif ($role4 == "approve") { ?>
                                                                                <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                        transition duration-150 ease-in-out origin-top-left
                                                                                        min-w-32 text-gray-950
                                                                                        ">
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/gm/pending.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../tender/gm/reports.php">Reports</a>
                                                                                    </li>
                                                                                </ul>
                                                                            <?php }

                                                                            $host = "127.0.0.1";
                                                                            $username = "root";
                                                                            $password = "";
                                                                            $db = "dms";
                                                                            $conn = mysqli_connect($host, $username, $password, $db);
                                                                            if ($conn->connect_error) die($conn->connect_error);
                                                                            $query = mysqli_query($conn, "SELECT * FROM bid_update ");
                                                                            $count = mysqli_num_rows($query);
                                                                            if (!$query) {
                                                                                echo mysqli_error($conn);
                                                                            } else {
                                                                                while ($row = mysqli_fetch_array($query)) {
                                                                                    $user1 = $row['user1'];
                                                                                    $user2 = $row['user2'];
                                                                                    $user3 = $row['user3'];
                                                                                    $user4 = $row['user4'];
                                                                                    $user5 = $row['user5'];
                                                                                    $user6 = $row['user6'];
                                                                                    $user7 = $row['user7'];
                                                                                    $user8 = $row['user8'];
                                                                                    $user9 = $row['user9'];
                                                                                    $user10 = $row['user10'];
                                                                                    if (($_SESSION['username'] == $user1 || $_SESSION['username'] == $user2 || $_SESSION['username'] == $user3 || $_SESSION['username'] == $user4 || $_SESSION['username'] == $user5 ||
                                                                                            $_SESSION['username'] == $user6 ||     $_SESSION['username'] == $user7 || $_SESSION['username'] == $user8 || $_SESSION['username'] == $user9 || $_SESSION['username'] == $user10) || ($role4 == 'request' || $role4 == 'authorise')
                                                                                    ) {
                                                                                        ?>
                                                                                        <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                        transition duration-150 ease-in-out origin-top-left
                                                                                        min-w-32 text-gray-950
                                                                                        ">
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a
                                                                                                    href="../../tender/committee/pending_committee.php">Pending
                                                                                                    Committee</a>
                                                                                            </li>
                                                                                            <li
                                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                                <a
                                                                                                    href="../../tender/committee/reports.php">Reports</a>
                                                                                            </li>
                                                                                        </ul>
                                                                                    <?php    } //if
                                                                                } // while
                                                                            } //else
                                                                            ?>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                <?php
                                                                                if (($section_code == "IT100" && $role2 == "IT1002" && $role1 == "") || ($section_code == "SAC300" && $role2 == "SAC3002" && $role1 == "") || ($section_code == "SAR300" && $role2 == "SAR3002" && $role1 == "") || ($section_code == "CC300" && $role2 == "CC3002" && $role1 == "") || ($section_code == "HR500" && $role2 == "HR5002" && $role1 == "") || ($section_code == "RM600" && $role2 == "RM6002" && $role1 == "") || ($section_code == "COM700" && $role2 == "COM7002" && $role1 == "") || ($section_code == "ENG800" && $role2 == "ENG8002" && $role1 == "")) { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } //innerif termination
                                                                                else if (($section_code == "IT100" && $role1 == "IT1001" && $role2 == "") || ($section_code == "SAC300" && $role1 == "SAC3001" && $role2 == "") || ($section_code == "SAR300" && $role1 == "SAR3001" && $role2 == "") || ($section_code == "CC300" && $role1 == "CC3001" && $role2 == "") || ($section_code == "HR500" && $role1 == "HR5001" && $role2 == "") || ($section_code == "RM600" && $role1 == "RM6001" && $role2 == "") || ($section_code == "COM700" && $role1 == "COM7001" && $role2 == "") || ($section_code == "ENG800" && $role1 == "ENG8001" && $role2 == "")) { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php }
                                                                                else if (($section_code == "IT100" && $role1 == "IT1001" && $role2 == "IT1002")
                                                                                    || ($section_code == "SAC300" && $role1 == "SAC3001" && $role2 == "SAC002")
                                                                                    || ($section_code == "SAR300" && $role1 == "SAR3001" && $role2 == "SAR3002")
                                                                                    || ($section_code == "CC300" && $role1 == "CC3001" && $role2 == "CC3002")
                                                                                    || ($section_code == "HR500" && $role1 == "HR5001" && $role2 == "HR5002")
                                                                                    || ($section_code == "RM600" && $role1 == "RM6001" && $role2 == "RM6002")
                                                                                    || ($section_code == "COM700" && $role1 == "COM7001" && $role2 == "COM7002")
                                                                                    || ($section_code == "ENG800" && $role1 == "ENG8001" && $role2 == "ENG8002")
                                                                                ) { ?>
                                                                                    <!-- error here -->
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } //2nnd inner elseif end
                                                                                elseif ($section_code == "CC900" && $role2 == "CC9002" && $role1 == "") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_accounts.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php }

                                                                                //district cashiers
                                                                                elseif (($section_code == "MTD" || $section_code == "MND" || $section_code == "MSD") && $role2 == "CC9002") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_accounts.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif (($section_code == "MTD" || $section_code == "MND" || $section_code == "MSD") && $role2 == "audit") { ?>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } //2nnd inner elseif end UPTO HERE
                                                                                elseif (($section_code == 'MTD' || $section_code == 'MND' || $section_code == 'MSD') && $role1 == "create") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_acquittal.php">Pending
                                                                                            Acquittal</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif (($section_code == 'MTD' || $section_code == 'MND' || $section_code == 'MSD') && $role2 == "DM001") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/reports.php">Reports</a>
                                                                                    </li>

                                                                                <?php } ?>
                                                                            </ul>
                                                                        </li>
                                                                    </ul>
                                                                </li>
                                                                <!-- PURCHASE ABOVE END -->

                                                                <!-- INVOICE VERIFICATION START -->
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span class="pr-1 flex-1">INVOICE
                                                                                VERIFICATION</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                            transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">

                                                                        <?php
                                                                        if ($role8 == "create") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../Invoice_verification_finale/supplier.php">Create</a>
                                                                            </li>
                                                                        <?php } ?>

                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span
                                                                                        class="pr-1 flex-1">VIEW</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                        transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                                min-w-32 text-gray-950
                                                                                                ">
                                                                                <?php if ($role8 == "create") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../Invoice_verification_finale/pending_approval.php">Verification
                                                                                            Progress Status</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif ($role8 == "audit") { ?>

                                                                                <?php } elseif ($role8 == "check") { ?>
                                                                                    <!--div class="dropdown-menu">
                                                                                            <button class="dropdown-item" type="button"><a href="../../Invoice_Verification/finance/reports.php">Reports</a></button-->

                                                                                    <?php
                                                                                } elseif ($role8 == "approve") { ?>

                                                                                <?php } else {
                                                                                }
                                                                                ?>
                                                                            </ul>

                                                                        </li>

                                                                    </ul>
                                                                </li>
                                                                <!-- INVOICE VERIFICATION END -->

                                                                <!-- PETTY CASH START -->
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                        <span class="pr-1 flex-1">PETTY CASH</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                            transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                        <?php
                                                                        if ($role1 == "create" || $role1 == "CA" || $role1 == "CD" || $role1 == "CAD") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../pettycash/pettyCash.php">Create</a>
                                                                            </li>
                                                                            <?php
                                                                        } else {
                                                                        }
                                                                        ?>
                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span
                                                                                        class="pr-1 flex-1">VIEW</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                        transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                                min-w-32 text-gray-950
                                                                                                ">

                                                                                <?php
                                                                                if ($role1 == "create") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif ($role1 == "audit") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } else if ($role1 == "CA") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/reports_CA.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } else if ($role1 == "CD") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_acquittal.php">Pending
                                                                                            Clearance(R)</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_accounts.php">Pending
                                                                                            Disbursement</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_clearance.php">Awaiting
                                                                                            Receipts</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_acquittal.php">Pending
                                                                                            Clearance(C)</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/reportsCD.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } //inner if termination
                                                                                else if ($role1 == "approve") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/reports.php">Reports</a>
                                                                                    </li>

                                                                                    <?php
                                                                                } //inner elseif termination

                                                                                else if ($role1 == "accountant") {
                                                                                    ?>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accountant/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accountant/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accountant/reports.php">Reports</a>
                                                                                    </li>

                                                                                    <?php
                                                                                } //inner elseif termination

                                                                                //Petty cash authoriser
                                                                                else if ($role1 == "authoriser") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/authoriser/pending_accounts.php">Pending
                                                                                            Authorisation**</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/authoriser/reports.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } //inner elseif termination

                                                                                //regional sections cashier
                                                                                elseif ($role1 == "disburse") {
                                                                                    ?>

                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_accounts.php">Pending
                                                                                            Disbursement</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_clearance.php">Awaiting
                                                                                            Receipts</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } elseif ($role1 == "supervisor") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/supervisor/pending_accounts.php">Pending
                                                                                            Disbursement</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_clearance.php">Awaiting
                                                                                            Receipts</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/supervisor/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/supervisor/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php } elseif ($role1 == "AD") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_accounts.php">Pending
                                                                                            Disbursement</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_clearance.php">Awaiting
                                                                                            Receipts</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_acquittal.php">Pending
                                                                                            Clearance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/reports_AD.php">Reports</a>
                                                                                    </li>
                                                                                <?php } elseif ($role1 == "CAD") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/section/pending_sectionhead.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/user/pending_acquittal.php">Pending
                                                                                            Clearance(R)</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_clearance.php">Awaiting
                                                                                            Receipts</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_accounts.php">Pending
                                                                                            Disbursement</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/pending_acquittal.php">Pending
                                                                                            Clearance(C)</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../pettycash/accounts/reports_AD.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } else {
                                                                                } ?>

                                                                            </ul>

                                                                        </li>

                                                                    </ul>
                                                                </li>
                                                                <!-- PETTY CASH END -->

                                                                <!-- RESTRICTED BIDDING START -->
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span class="pr-1 flex-1">RESTRICTED
                                                                                BIDDING</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                            transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                        <?php
                                                                        if ($role7 == "create") { ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a
                                                                                    href="../../restricted/requester/request.php">Create</a>
                                                                            </li>
                                                                            <?php
                                                                        } else {
                                                                        }
                                                                        ?>
                                                                        <li
                                                                            class="relative px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <button
                                                                                class="w-full text-left flex items-center outline-none focus:outline-none">
                                                                                    <span
                                                                                        class="pr-1 flex-1">VIEW</span>
                                                                                <span class="mr-auto">
                                                                                        <svg class="fill-current h-4 w-4
                                                                                                        transition duration-150 ease-in-out"
                                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                                             viewBox="0 0 20 20">
                                                                                            <path
                                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                        </svg>
                                                                                    </span>
                                                                            </button>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                                min-w-32 text-gray-950
                                                                                                ">

                                                                                <?php
                                                                                if ($role7 == "create") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a href="">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <?php
                                                                                }
                                                                                //Section Head
                                                                                elseif ($role7 == "authorise") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/section/pending_section.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/section/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php }
                                                                                //Procurement Officer
                                                                                elseif ($role7 == "process") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/procurement/pending_procurement.php">Pending
                                                                                            Procurement</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/section/pending_section.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/procurement/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php }
                                                                                //Finance Manager
                                                                                elseif ($role7 == "confirm") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/finance/pending_finance.php">Pending
                                                                                            Finance</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/finance/reports.php">Reports</a>
                                                                                    </li>
                                                                                <?php }
                                                                                //General Manager
                                                                                elseif ($role7 == "approve") {
                                                                                    ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/gm/pending_gm.php">Pending
                                                                                            Approval</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../restricted/gm/reports.php">Reports</a>
                                                                                    </li>

                                                                                    <?php
                                                                                } else {
                                                                                } ?>

                                                                            </ul>

                                                                        </li>

                                                                    </ul>
                                                                </li>
                                                                <!-- RESTRICTED BIDDING END -->

                                                                <!-- REMITTANCE ADVICE START -->
                                                                <?php
                                                                switch ($role) {
                                                                    case "prepare":
                                                                    case "check":
                                                                    case "authorise":
                                                                    case "pay":
                                                                        ?>
                                                                        <li
                                                                            class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                            <a
                                                                                class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span class="pr-1 flex-1">REMITTANCE
                                                                                ADVICE</span>
                                                                                <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                            transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                            </a>
                                                                            <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                    transition duration-150 ease-in-out origin-top-left
                                                                                    min-w-32 text-gray-950
                                                                                    ">
                                                                                <?php
                                                                                if ($role == "prepare") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/requester/pending_remittance.php">Create</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/requester/pending_checking.php">Edit</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/requester/report.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } elseif ($role == "audit") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/requester/report.php">Reports</a>
                                                                                    </li>
                                                                                <?php } else if ($role == "check") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/checker/pending_checking.php">Pending
                                                                                            Checking</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/checker/report.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } else if ($role == "authorise") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/authoriser/pending_authorisation.php">Pending
                                                                                            Authorisation</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/authoriser/report.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                } else if ($role == "pay") { ?>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/payer/pending_payment.php">Pending
                                                                                            Payment</a>
                                                                                    </li>
                                                                                    <li
                                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                        <a
                                                                                            href="../../remittance/datatables/production/payer/report.php">Reports</a>
                                                                                    </li>
                                                                                    <?php
                                                                                }
                                                                                ?>

                                                                            </ul>
                                                                        </li>
                                                                        <?php
                                                                        break;
                                                                    default:
                                                                }
                                                                ?>
                                                                <!-- REMITTANCE ADVICE END -->

                                                            </ul>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- More products... -->
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>

                        <!-- FINANCE END -->
                        <!-- ENGINEERING START -->

                        <div class="w-auto bg-gray-200 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
                            <div class="sm:flex lg:items-center lg:justify-between">
                                <div class="min-w-0 flex-1">
                                    <div class="">
                                        <div class="mx-auto">

                                            <div class="group relative">
                                                <div
                                                    class="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-md bg-gray-200 lg:aspect-none group-hover:opacity-75 lg:h-40">
                                                    <img src="../../assets/imgs/electrical.jpg" alt=""
                                                         class="h-full w-full object-cover object-center lg:h-full lg:w-full">
                                                </div>
                                                <div class="mt-4 flex justify-center">
                                                    <div class="w-full ">
                                                        <div
                                                            class="dropdown-group inline-block w-full text-blue-50">
                                                            <button
                                                                class="w-full bg-blue-800 hover:bg-blue-900 outline-none focus:outline-none border px-3 py-1 rounded flex items-center">
                                                                    <span
                                                                        class="pr-1 font-semibold flex-1 text-blue-50">ENGINEERING</span>
                                                                <span class="text-blue-50">
                                                                        <svg class="fill-current h-4 w-4 transform group-hover:-rotate-180
                                                                                transition duration-150 ease-in-out"
                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                             viewBox="0 0 20 20">
                                                                            <path
                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                        </svg>
                                                                    </span>
                                                            </button>


                                                            <ul style="min-width: 18rem;"
                                                                class="bg-blue-50 z-10 text-gray-950 border rounded transform scale-0 group-hover:scale-100 absolute
                                                                            transition duration-150 ease-in-out origin-top">
                                                                <li
                                                                    class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a tabindex="-1"
                                                                       href="http://192.168.15.236/">GIS</a>
                                                                </li>
                                                                <?php if ($role7 == "foreman") { ?>
                                                                    <li
                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                        <a tabindex="-1"
                                                                           href="../../fleet/service/foreman/foreman_create_job.php">Fleet
                                                                            Management</a>
                                                                    </li>
                                                                <?php } else if ($role7 == "mechanic") { ?>
                                                                    <li
                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                        <a tabindex="-1"
                                                                           href="../../fleet/service/artisan/assignee.php">Fleet
                                                                            Management</a>
                                                                    </li>
                                                                <?php } else if ($role7 == "officer") { ?>
                                                                    <li
                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                        <a tabindex="-1"
                                                                           href="../../fleet/internal_vehicles.php">Fleet
                                                                            Management</a>
                                                                    </li>
                                                                <?php } else if ($role7 == "create") { ?>
                                                                    <li
                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                        <a tabindex="-1"
                                                                           href="../../fleet/service/service/booking.php">Fleet
                                                                            Management</a>
                                                                    </li>
                                                                <?php } else if ($role7 == "clerk") { ?>
                                                                    <li
                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                        <a tabindex="-1"
                                                                           href="../../fleet/logbook.php">Fleet
                                                                            Management</a>
                                                                    </li>
                                                                <?php } else if ($role7 == "costing") { ?>
                                                                    <li
                                                                        class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                        <a tabindex="-1"
                                                                           href="../../fleet/service/costing/cost.php">Fleet
                                                                            Management</a>
                                                                    </li>
                                                                <?php } ?>
                                                            </ul>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- More products... -->
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>

                        <!-- ENGINEERING END -->
                        <!-- IT START -->

                        <div class="w-auto bg-gray-200 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
                            <div class="sm:flex lg:items-center lg:justify-between">
                                <div class="min-w-0 flex-1">
                                    <div class="">
                                        <div class="mx-auto">

                                            <div class="group relative">
                                                <div
                                                    class="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-md bg-gray-200 lg:aspect-none group-hover:opacity-75 lg:h-40">
                                                    <img src="../../assets/imgs/electrical.jpg" alt=""
                                                         class="h-full w-full object-cover object-center lg:h-full lg:w-full">
                                                </div>
                                                <div class="mt-4 flex justify-center">
                                                    <div class="w-full ">
                                                        <div
                                                            class="dropdown-group inline-block w-full text-blue-50">
                                                            <button
                                                                class="w-full bg-blue-800 hover:bg-blue-900 outline-none focus:outline-none border px-3 py-1 rounded flex items-center">
                                                                    <span
                                                                        class="pr-1 font-semibold flex-1 text-blue-50">IT</span>
                                                                <span class="text-blue-50">
                                                                        <svg class="fill-current h-4 w-4 transform group-hover:-rotate-180
                                                                                transition duration-150 ease-in-out"
                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                             viewBox="0 0 20 20">
                                                                            <path
                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                        </svg>
                                                                    </span>
                                                            </button>


                                                            <ul style="min-width: 18rem;"
                                                                class="bg-blue-50 z-10 text-gray-950 border rounded transform scale-0 group-hover:scale-100 absolute
                                                                            transition duration-150 ease-in-out origin-top">
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span
                                                                                class="pr-1 flex-1">ADMINISTRATION</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                        transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                min-w-32 text-gray-950
                                                                                ">
                                                                        <?php if ($roles == 'admin') {
                                                                            ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../users/create.php">New
                                                                                    User</a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../users/update.php">Edit
                                                                                    User</a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../users/password.php">Reset
                                                                                    Password</a>
                                                                            </li>
                                                                            <?php
                                                                        }  ?>

                                                                    </ul>
                                                                </li>
                                                            </ul>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- More products... -->
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>

                        <!-- IT END -->
                        <!-- HR START -->

                        <div class="w-auto bg-gray-200 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
                            <div class="sm:flex lg:items-center lg:justify-between">
                                <div class="min-w-0 flex-1">
                                    <div class="">
                                        <div class="mx-auto">

                                            <div class="group relative">
                                                <div
                                                    class="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-md bg-gray-200 lg:aspect-none group-hover:opacity-75 lg:h-40">
                                                    <img src="../../assets/imgs/electrical.jpg" alt=""
                                                         class="h-full w-full object-cover object-center lg:h-full lg:w-full">
                                                </div>
                                                <div class="mt-4 flex justify-center">
                                                    <div class="w-full ">
                                                        <div
                                                            class="dropdown-group inline-block w-full text-blue-50">
                                                            <button
                                                                class="w-full bg-blue-800 hover:bg-blue-900 outline-none focus:outline-none border px-3 py-1 rounded flex items-center">
                                                                    <span
                                                                        class="pr-1 font-semibold flex-1 text-blue-50">HR</span>
                                                                <span class="text-blue-50">
                                                                        <svg class="fill-current h-4 w-4 transform group-hover:-rotate-180
                                                                                transition duration-150 ease-in-out"
                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                             viewBox="0 0 20 20">
                                                                            <path
                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                        </svg>
                                                                    </span>
                                                            </button>


                                                            <ul style="min-width: 18rem;"
                                                                class="bg-blue-50 z-10 text-gray-950 border rounded transform scale-0 group-hover:scale-100 absolute
                                                                            transition duration-150 ease-in-out origin-top">

                                                            </ul>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- More products... -->
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>

                        <!-- HR END -->
                        <!-- RISK START -->

                        <div class="w-auto bg-gray-200 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
                            <div class="sm:flex lg:items-center lg:justify-between">
                                <div class="min-w-0 flex-1">
                                    <div class="">
                                        <div class="mx-auto">

                                            <div class="group relative">
                                                <div
                                                    class="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-md bg-gray-200 lg:aspect-none group-hover:opacity-75 lg:h-40">
                                                    <img src="../../assets/imgs/electrical.jpg" alt=""
                                                         class="h-full w-full object-cover object-center lg:h-full lg:w-full">
                                                </div>
                                                <div class="mt-4 flex justify-center">
                                                    <div class="w-full ">
                                                        <div
                                                            class="dropdown-group inline-block w-full text-blue-50">
                                                            <button
                                                                class="w-full bg-blue-800 hover:bg-blue-900 outline-none focus:outline-none border px-3 py-1 rounded flex items-center">
                                                                    <span
                                                                        class="pr-1 font-semibold flex-1 text-blue-50">RISK</span>
                                                                <span class="text-blue-50">
                                                                        <svg class="fill-current h-4 w-4 transform group-hover:-rotate-180
                                                                                transition duration-150 ease-in-out"
                                                                             xmlns="http://www.w3.org/2000/svg"
                                                                             viewBox="0 0 20 20">
                                                                            <path
                                                                                d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                        </svg>
                                                                    </span>
                                                            </button>
                                                            <ul style="min-width: 18rem;"
                                                                class="bg-blue-50 z-10 text-gray-950 border rounded transform scale-0 group-hover:scale-100 absolute
                                                                            transition duration-150 ease-in-out origin-top">
                                                                <li
                                                                    class="relative px-1 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                    <a
                                                                        class="w-full text-left px-3 flex items-center outline-none focus:outline-none">
                                                                            <span
                                                                                class="pr-1 flex-1">Non Conformity</span>
                                                                        <span class="mr-auto">
                                                                                <svg class="fill-current h-4 w-4
                                                                                        transition duration-150 ease-in-out"
                                                                                     xmlns="http://www.w3.org/2000/svg"
                                                                                     viewBox="0 0 20 20">
                                                                                    <path
                                                                                        d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                                                                </svg>
                                                                            </span>
                                                                    </a>
                                                                    <ul class="bg-blue-50 border rounded-sm absolute top-0 right-0
                                                                                transition duration-150 ease-in-out origin-top-left
                                                                                min-w-32 text-gray-950
                                                                                ">
                                                                        <?php if ($role6=='originator'){ ?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/recipient/new.php">Create Non Conformity
                                                                                </a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/recipient/new.php">New Ncs
                                                                                </a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/recipient/reports.php">Reports</a>
                                                                            </li>
                                                                        <?php }else if($role6=='recipient'){?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/nonconformity.php">Create Non Conformity
                                                                                </a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/recipient/new.php">New Ncs
                                                                                </a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/reports.php">Reports</a>
                                                                            </li>
                                                                            <!-- <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                    href="../users/password.php">Reset
                                                                                    Password</a>
                                                                            </li> -->
                                                                        <?php } elseif($role6=='supervisor'){?>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/nonconformity.php">Create Non Conformity
                                                                                </a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/recipient/new.php">New Ncs
                                                                                </a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/supervisor/new.php">Review NCs</a>
                                                                            </li>
                                                                            <li
                                                                                class="px-3 py-1 hover:bg-blue-550 rounded m-1 hover:text-blue-50">
                                                                                <a tabindex="-1"
                                                                                   href="../../NonConformity/reports.php">Reports</a>
                                                                            </li>
                                                                            <?php
                                                                        }  ?>

                                                                    </ul>
                                                                </li>
                                                            </ul>
                                                            <!-- <button class="dropdown-item dropdown-toggle test1" type="button" data-toggle="dropdown">Non Conformity</button>
                                                                    <?php if ($role6=='originator'){ ?>
                                                        <div class="dropdown-menu">
                                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/nonconformity.php">Create</a></button>
                                                                    <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/recipient/new.php">New NC`s</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/recipient/reports.php">Reports</a></button>
                                            </div>
                                        <?php }else if($role6=='recipient'){?>
                                            <div class="dropdown-menu">
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/nonconformity.php">Create</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/recipient/new.php">New NC`s</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/recipient/reports.php">Reports</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/reports.php">all NC's(new)</a></button>

                                            </div>
                                        <?php } elseif($role6=='supervisor'){?>
                                            <div class="dropdown-menu">
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/nonconformity.php">Create</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/recipient/new.php">New NC`s</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/supervisor/new.php">Review NC`s</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/supervisor/reports.php">Reports</a></button>
                                                <button class="dropdown-item" type="button"><a tabindex="-1" href="../../NonConformity/reports.php">all NC's(new)</a></button>
                                            </div>
                                        <?php }?> -->


                                                            <ul style="min-width: 18rem;"
                                                                class="bg-blue-50 z-10 text-gray-950 border rounded transform scale-0 group-hover:scale-100 absolute
                                                                            transition duration-150 ease-in-out origin-top">

                                                            </ul>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- More products... -->
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>

                        <!-- RISK END -->
                    </div>

                </div>

            </div>
        </div>
    </div>
</main>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</body>

</html>