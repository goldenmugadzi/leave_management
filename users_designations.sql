-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Jan 15, 2024 at 10:53 AM
-- Server version: 5.7.36
-- PHP Version: 7.4.26

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `beii`
--

-- --------------------------------------------------------

--
-- Table structure for table `users_designations`
--

DROP TABLE IF EXISTS `users_designations`;
CREATE TABLE IF NOT EXISTS `users_designations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `description` varchar(100) NOT NULL,
  `chk` varchar(100) NOT NULL,
  `identifier` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=149 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_designations`
--

INSERT INTO `users_designations` (`id`, `description`, `chk`, `identifier`) VALUES
(2, 'Accounting - Clerk', '0', '0'),
(3, 'Accounting Officer - Billing', '0', '1'),
(4, 'Accounting Officer - Cash', '0', '2'),
(5, 'Accounting Officer - Cost', '0', '3'),
(6, 'Accounting Officer - Costing', '0', '0'),
(7, 'Accounting Officer - Costs/Budgets', '0', '0'),
(8, 'Accounting Officer - Creditors', '0', '0'),
(9, 'Accounting Officer - Payments', '0', '0'),
(10, 'Accounting Officer - Revenue', '0', '4'),
(11, 'Accounts Clerk', '0', '0'),
(12, 'Administration Officer', '0', '6'),
(13, 'Apprentice', '0', '7'),
(14, 'Artisan', '0', '8'),
(15, 'Artisan - Auto', '0', '9'),
(16, 'Artisan - Cable Jointer', '0', '0'),
(17, 'Artisan - Civil', '0', '10'),
(18, 'Artisan - Electrical', '0', '11'),
(19, 'Artisan - Inspector', '0', '0'),
(20, 'Artisan - Lines', '0', '12'),
(21, 'Artisan - Mechanic', '0', '0'),
(22, 'Artisan - Motor Mech', '0', '13'),
(23, 'Artisan - Substation', '0', '0'),
(24, 'Artisan Assistant - Auto', '0', '14'),
(25, 'Artisan Assistant - Cable Jointer', '0', '0'),
(26, 'Artisan Assistant - Civil', '0', '15'),
(27, 'Artisan Assistant - Electrical', '0', '16'),
(28, 'Artisan Assistant - Lines', '0', '17'),
(29, 'Artisan Assistant - Mechanic', '0', '0'),
(30, 'Artisan Assistant - Motor Mech', '0', '18'),
(31, 'Artisan Assistant - Power Cables', '0', '0'),
(32, 'Attachee', '0', '19'),
(33, 'Auger - Crane Operator', '0', '0'),
(34, 'Back Office Supervisor', '0', '0'),
(35, 'Banking Hall Supervisor', '0', '0'),
(36, 'Buyer', '0', '0'),
(37, 'Chief Risk Officer', '0', '21'),
(38, 'Clerk', '0', '22'),
(39, 'Clerk - Admin', '0', '23'),
(40, 'Clerk - Cash', '0', '24'),
(41, 'Clerk - Commercial', '0', '25'),
(42, 'Clerk - Costs', '0', '26'),
(43, 'Clerk - Personnel', '0', '27'),
(44, 'Clerk - Records', '0', '28'),
(45, 'Clerk - Revenue Assurance', '0', '29'),
(46, 'Clerk - Sales', '0', '30'),
(47, 'Clerk - Stores', '0', '31'),
(48, 'Clerk - Typist', '0', '32'),
(49, 'Clerk Typist', '0', '0'),
(50, 'Clients Services Officer', '0', '33'),
(51, 'Commercial Clerk', '0', '0'),
(52, 'Commercial Engineer', '0', '34'),
(53, 'Commercial Manager', '0', '35'),
(54, 'Commercial Officer', '0', '36'),
(55, 'Commercial Supervisor', '0', '37'),
(56, 'Commercial  Supervisor', '0', '0'),
(57, 'Commissionaire', '0', '0'),
(58, 'Customer Care Clerk', '0', '38'),
(59, 'Customer Liaison Attendant', '0', '0'),
(60, 'Customer Services Engineer', '0', '0'),
(61, 'Depot Clerk', '0', '39'),
(62, 'District Manager', '0', '40'),
(63, 'Divisional Secretary', '0', '0'),
(64, 'Draughtsperson', '0', '41'),
(65, 'Engineer', '0', '42'),
(66, 'Engineering Manager', '0', '43'),
(67, 'Finance Manager', '0', '44'),
(68, 'Fuel Attendant', '0', '0'),
(69, 'Gang Charge', '0', '0'),
(70, 'Garage Foreperson', '0', '45'),
(71, 'General Manager', '0', '46'),
(72, 'General Worker', '0', '0'),
(73, 'GIS Artisan (Contract)', '0', '47'),
(74, 'GIS Engineer', '0', '48'),
(75, 'GIS Technician', '0', '49'),
(76, 'Guest House Caretaker', '0', '0'),
(77, 'Hardware Technician', '0', '51'),
(78, 'Hardware Technician Assistant', '0', '0'),
(79, 'Health and Safety Officer', '0', '52'),
(80, 'Heavy Duty Driver', '0', '53'),
(81, 'HRAM', '0', '54'),
(82, 'Human Resource Officer', '0', '55'),
(83, 'Industrial Relations Officer', '0', '56'),
(84, 'Lead Artisan', '0', '57'),
(85, 'Lineworker', '0', '58'),
(86, 'Loss Control Assistant', '0', '59'),
(87, 'Loss Control Officer', '0', '60'),
(88, 'Loss Control Officer - Investigations', '0', '0'),
(89, 'Loss Control Officer - Operations', '0', '0'),
(90, 'Loss Controller', '0', '61'),
(91, 'Maintenance Engineer', '0', '62'),
(92, 'Marketing Officer', '0', '63'),
(93, 'Messenger', '0', '64'),
(94, 'Messenger - Cleaner', '0', '0'),
(95, 'Network Development Engineer', '0', '65'),
(96, 'Operations & Maintenance Engineer', '0', '0'),
(97, 'Panel Beater', '0', '66'),
(98, 'Personnel Clerk', '0', '67'),
(99, 'Personnel Officer', '0', '68'),
(100, 'Postgraduate Trainee', '0', '69'),
(101, 'Principal Technician', '0', '70'),
(102, 'Principal Technician - Drawing Office', '0', '0'),
(103, 'Principal Technician - Project Mgt', '0', '0'),
(104, 'Procurement Officer', '0', '71'),
(105, 'Revenue Assurance - Clerk', '0', '0'),
(106, 'Revenue Assurance Assistant', '0', '72'),
(107, 'Risk Officer', '0', '73'),
(108, 'Safety Health and Environment', '0', '0'),
(109, 'Sales Analyst', '0', '74'),
(110, 'Sales Executive', '0', '75'),
(111, 'Secretary', '0', '76'),
(112, 'Senior Accountant - FM', '0', '0'),
(113, 'Senior Accountant - MA', '0', '0'),
(114, 'Senior Client Services Officer', '0', '79'),
(115, 'Senior Engineer', '0', '80'),
(116, 'Senior Engineer - Operations and Maintenance', '0', '81'),
(117, 'Senior Engineer - Planning and Design', '0', '82'),
(118, 'Senior Engineer - Projects', '0', '83'),
(119, 'Senior Engineer- Operations', '0', '0'),
(120, 'Senior Foreperson', '0', '84'),
(121, 'Senior Foreperson - Mains', '0', '0'),
(122, 'Senior Foreperson - Substations', '0', '0'),
(123, 'Senior Loss Control Officer', '0', '85'),
(124, 'Senior System Controller', '0', '0'),
(125, 'Storekeeper', '0', '86'),
(126, 'Stores Assistant', '0', '87'),
(127, 'Stores Assistants', '0', '0'),
(128, 'Stores Clerk', '0', '88'),
(129, 'Stores Officer', '0', '0'),
(130, 'Supplies Officer', '0', '0'),
(131, 'Switchboard Operator', '0', '89'),
(132, 'Systems Administrator', '0', '90'),
(133, 'Systems Support Officer', '0', '91'),
(134, 'Technical Clerk', '0', '92'),
(135, 'Technician', '0', '93'),
(136, 'Technician - Drawing Office', '0', '0'),
(137, 'Technician - Energy', '0', '0'),
(138, 'Technician - Planning & Design', '0', '0'),
(139, 'Technician - Planning and Design', '0', '94'),
(140, 'Technician - Projects', '0', '0'),
(141, 'Technician - Substations', '0', '0'),
(142, 'Technician Assistant', '0', '95'),
(143, 'Technician Assistant - Substations', '0', '0'),
(144, 'Test', '0', '96'),
(145, 'Transport Controller', '0', '97'),
(146, 'Transport Officer', '0', '98'),
(147, 'worker', '0', '0'),
(148, 'Worker - Grounds', '0', '0');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
