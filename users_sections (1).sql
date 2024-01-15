-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Jan 15, 2024 at 10:55 AM
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
-- Table structure for table `users_sections`
--

DROP TABLE IF EXISTS `users_sections`;
CREATE TABLE IF NOT EXISTS `users_sections` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `section` varchar(100) NOT NULL,
  `code` varchar(100) NOT NULL,
  `district_id` varchar(100) NOT NULL,
  `region_id` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=13 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_sections`
--

INSERT INTO `users_sections` (`id`, `section`, `code`, `district_id`, `region_id`) VALUES
(1, 'GM Office', '521001', '', ''),
(2, 'Finance', '522001', '', ''),
(3, 'Stores', '522102', '', ''),
(4, 'Procurement', '522301', '', ''),
(5, 'Human Resource', '523001', '', ''),
(6, 'Engineering', '524001', '', ''),
(7, 'Network Development', '524101', '', ''),
(8, 'Transport', '524202', '', ''),
(9, 'Operations and Maintenance', '524301', '', ''),
(10, 'Commercial', '525000', '', ''),
(11, 'Risk Management', '526001', '', ''),
(12, 'Information Technology', '527001', '', '');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
