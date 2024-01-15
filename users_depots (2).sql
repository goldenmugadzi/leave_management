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
-- Table structure for table `users_depots`
--

DROP TABLE IF EXISTS `users_depots`;
CREATE TABLE IF NOT EXISTS `users_depots` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `depot` varchar(100) NOT NULL,
  `code` varchar(100) NOT NULL,
  `district_id` varchar(100) NOT NULL,
  `region_id` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_depots`
--

INSERT INTO `users_depots` (`id`, `depot`, `code`, `district_id`, `region_id`) VALUES
(1, 'Mabelreign Depot', '524503', '2', '1'),
(2, 'Borrowdale Depot', '524703', '4', '1'),
(3, 'Glen View Depot', '524602', '3', '1'),
(4, 'Kuwadzana Depot', '524502', '2', '1'),
(5, 'Mabvuku Depot', '524704', '4', '1'),
(6, 'Ruwa Depot', '524705', '4', '1'),
(7, 'Southerton Depot', '524604', '3', '1'),
(8, 'Warren Park Depot', '524504', '2', '1'),
(9, 'Waterfalls Depot', '524603', '3', '1'),
(10, 'CBD Depot', '524702', '4', '1'),
(11, 'Makoni Depot', '524402', '1', '1'),
(12, 'Zengeza Depot', '524403', '1', '1'),
(13, 'Seke', '000000', '1', '1');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
