-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Mar 05, 2024 at 12:59 PM
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
-- Database: `beii_test`
--

-- --------------------------------------------------------

--
-- Table structure for table `ace_ace`
--

DROP TABLE IF EXISTS `ace_ace`;
CREATE TABLE IF NOT EXISTS `ace_ace` (
  `Department` varchar(100) DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `section` varchar(100) DEFAULT NULL,
  `allocation_code_of_expenditure` varchar(100) DEFAULT NULL,
  `details_of_expenditure` varchar(100) DEFAULT NULL,
  `amount` double DEFAULT NULL,
  `quotation1` varchar(100) NOT NULL,
  `quotation2` varchar(100) NOT NULL,
  `quotation3` varchar(100) NOT NULL,
  `requested_by` varchar(100) DEFAULT NULL,
  `date_created` date DEFAULT NULL,
  `Ace_id2` varchar(60) NOT NULL,
  `Ace_id` int(11) NOT NULL AUTO_INCREMENT,
  `approval_status` varchar(120) DEFAULT NULL,
  `approved_by` varchar(56) DEFAULT NULL,
  `rejected_by` varchar(56) DEFAULT NULL,
  `date_approved` date DEFAULT NULL,
  `date_rejected` date DEFAULT NULL,
  `rejection_reason` varchar(200) DEFAULT NULL,
  `section_head` varchar(30) DEFAULT NULL,
  `section_head_approval_status` varchar(40) DEFAULT NULL,
  `section_head_rejection_reason` longtext,
  `section_head_approval_date` date DEFAULT NULL,
  `accounting_officer` varchar(30) DEFAULT NULL,
  `accounting_officer_approval_status` varchar(40) DEFAULT NULL,
  `accounting_officer_rejection_reason` longtext,
  `accounting_officer_approval_date` date DEFAULT NULL,
  `finance_manager` varchar(60) DEFAULT NULL,
  `fm_approval_status` varchar(40) DEFAULT NULL,
  `fm_rejection_reason` varchar(200) DEFAULT NULL,
  `fm_date_approved` date DEFAULT NULL,
  `fm_date_rejected` date DEFAULT NULL,
  `general_manager` varchar(70) DEFAULT NULL,
  `gm_approval_status` varchar(50) DEFAULT NULL,
  `gm_approved` varchar(26) DEFAULT NULL,
  `gm_rejection_reason` varchar(400) DEFAULT NULL,
  `gm_approved_date` date DEFAULT NULL,
  `asset_number` longtext,
  `capital_estimated` double DEFAULT NULL,
  `capital_sanctioned` double DEFAULT NULL,
  `region` varchar(40) DEFAULT NULL,
  `classification` varchar(200) DEFAULT NULL,
  `present_tariff` double DEFAULT NULL,
  `present_fmc` varchar(200) DEFAULT NULL,
  `capital_contribution` double DEFAULT NULL,
  `materials` double DEFAULT NULL,
  `connection_fee` double DEFAULT NULL,
  `labour` double DEFAULT NULL,
  `transport` double DEFAULT NULL,
  `total_connection_fee` double DEFAULT NULL,
  `designation` varchar(200) DEFAULT NULL,
  `approval_code` int(11) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `budget_id_id` int(11) NOT NULL,
  PRIMARY KEY (`Ace_id`),
  KEY `Ace_ace_budget_id_id_f18359fe` (`budget_id_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `ace_ace`
--

INSERT INTO `ace_ace` (`Department`, `location`, `section`, `allocation_code_of_expenditure`, `details_of_expenditure`, `amount`, `quotation1`, `quotation2`, `quotation3`, `requested_by`, `date_created`, `Ace_id2`, `Ace_id`, `approval_status`, `approved_by`, `rejected_by`, `date_approved`, `date_rejected`, `rejection_reason`, `section_head`, `section_head_approval_status`, `section_head_rejection_reason`, `section_head_approval_date`, `accounting_officer`, `accounting_officer_approval_status`, `accounting_officer_rejection_reason`, `accounting_officer_approval_date`, `finance_manager`, `fm_approval_status`, `fm_rejection_reason`, `fm_date_approved`, `fm_date_rejected`, `general_manager`, `gm_approval_status`, `gm_approved`, `gm_rejection_reason`, `gm_approved_date`, `asset_number`, `capital_estimated`, `capital_sanctioned`, `region`, `classification`, `present_tariff`, `present_fmc`, `capital_contribution`, `materials`, `connection_fee`, `labour`, `transport`, `total_connection_fee`, `designation`, `approval_code`, `quantity`, `budget_id_id`) VALUES
('527001', NULL, NULL, '527001', 'Testing', 10, 'uploads/ace/Companies_Act_Chapter_24-03_updated.pdf', '', '', '12345', '2024-02-28', 'ACE2024022886', 1, 'approved by General Manager', '1', NULL, '2024-02-28', NULL, NULL, NULL, 'approved by section head', NULL, '2024-02-28', '1', 'approved by accounting officer', NULL, '2024-02-28', '1', 'approved by Finance Manager', NULL, '2024-02-28', NULL, '1', 'approved by General Manager', NULL, NULL, NULL, ',,,,,,,,,', NULL, NULL, 'Harare', 'internal', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '90', NULL, 10, 1);

-- --------------------------------------------------------

--
-- Table structure for table `ace_budget`
--

DROP TABLE IF EXISTS `ace_budget`;
CREATE TABLE IF NOT EXISTS `ace_budget` (
  `budget_id` int(11) NOT NULL AUTO_INCREMENT,
  `section_code` varchar(36) DEFAULT NULL,
  `section` varchar(36) DEFAULT NULL,
  `budget_name` varchar(200) DEFAULT NULL,
  `allocated` double DEFAULT NULL,
  `awaiting_sanctioning` double DEFAULT NULL,
  `withdrawn` double DEFAULT NULL,
  `to_be_withdrawn` double DEFAULT NULL,
  `balance` double DEFAULT NULL,
  `withdrawal_date` date DEFAULT NULL,
  `period` int(10) UNSIGNED NOT NULL,
  `region` varchar(36) DEFAULT NULL,
  `created_date` date DEFAULT NULL,
  `budget_note` varchar(100) NOT NULL,
  PRIMARY KEY (`budget_id`)
) ENGINE=MyISAM AUTO_INCREMENT=122 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `ace_budget`
--

INSERT INTO `ace_budget` (`budget_id`, `section_code`, `section`, `budget_name`, `allocated`, `awaiting_sanctioning`, `withdrawn`, `to_be_withdrawn`, `balance`, `withdrawal_date`, `period`, `region`, `created_date`, `budget_note`) VALUES
(1, '521001', 'GM', 'GM-computer', 194333420, 0, 0, 194333430, 194333420, '2024-02-28', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1.csv'),
(2, '521001', 'GM', 'GM-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_ELgvXwM.csv'),
(3, '521001', 'GM', 'GM-motor vehicles', 240250000, 0, 0, 0, 240250000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_cz95kpt.csv'),
(4, '522001', 'Finance', 'Finance- T&E', 127548725, 0, 0, 0, 127548725, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_XeoSI0w.csv'),
(5, '522001', 'Finance', 'Finance-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_uvGQ9VA.csv'),
(6, '522001', 'Finance', 'Finance-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_66Fecv3.csv'),
(7, '522001', 'Finance', 'Finance-motor vehicles', 480500000, 0, 0, 0, 480500000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_s7MV9z5.csv'),
(8, '523001', 'Human Resources', 'HR-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_uEiJczg.csv'),
(9, '523001', 'Human Resources', 'HR-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_qHw4yZ0.csv'),
(10, '523001', 'Human Resources', 'HR-motor vehicles', 480500000, 0, 0, 0, 480500000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_I34bNU2.csv'),
(11, '523001', 'Human Resources', 'HR-L&B', 4723449600, 700000000, 0, 0, 4723449600, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_ggnrQyA.csv'),
(12, '524001', 'EM', 'EM-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_DU5xeau.csv'),
(13, '524001', 'EM', 'EM-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_8gyszKU.csv'),
(14, '524001', 'EM', 'EM-motor vehicles', 240250000, 0, 0, 0, 240250000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_TuLzIvu.csv'),
(15, '524101', 'Network Development', 'Projects-T&E', 127548725, 0, 0, 0, 127548725, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_x1Pgdlp.csv'),
(16, '524101', 'Network Development', 'Projects-computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_TtljP32.csv'),
(17, '524101', 'Network Development', 'Projects-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_h9yAGxS.csv'),
(18, '524101', 'Network Development', 'Projects-motor vehicles', 1441500000, 0, 0, 0, 1441500000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_qkSBvOC.csv'),
(19, '524101', 'Network Development', 'Projects-Category 1', 50510764800, 0, 0, 0, 50510764800, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_o3Nykq1.csv'),
(20, '524101', 'Network Development', 'Projects-Category 3', 128000000000, 0, 0, 0, 128000000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_VeEtw9H.csv'),
(21, '524301', 'Operation and Maintenance', 'OPS- T&E', 819956144.2, 0, 0, 0, 819956144.2, '2024-01-17', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_fXgVvzm.csv'),
(22, '524301', 'Operation and Maintenance', 'OPS-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_M4PlD65.csv'),
(23, '524301', 'Operation and Maintenance', 'OPS-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_qsByS6w.csv'),
(24, '524301', 'Operation and Maintenance', 'OPS-motor vehicles', 2306400000, 0, 0, 0, 2306400000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_8QEjRga.csv'),
(25, '524401', 'Chitungwiza', 'Zengeza- T&E', 409978072.1, 0, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_oV0rR7h.csv'),
(26, '524401', 'Chitungwiza', 'Zengeza-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_G7xI2Ic.csv'),
(27, '524401', 'Chitungwiza', 'Zengeza-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_84O35lT.csv'),
(28, '524401', 'Chitungwiza', 'Zengeza-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_cGTAMKZ.csv'),
(29, '524401', 'Chitungwiza', 'Zengeza-Category 2', 1368000000, 0, 0, 0, 1368000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_6guUMBb.csv'),
(30, '524401', 'Chitungwiza', 'Zengeza-Major Distribution Maintenace Equipment', 4713430656, 0, 0, 0, 4713430656, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_lk6oMoF.csv'),
(31, '524401', 'Chitungwiza', 'Seke- T&E', 409978072.1, 7000000, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_4K8sdO8.csv'),
(32, '524401', 'Chitungwiza', 'Seke-computer', 194333420, 0, 0, 0, 194333420, '2024-01-17', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_oxQXDJq.csv'),
(33, '524401', 'Chitungwiza', 'Seke-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_xtIXecJ.csv'),
(34, '524401', 'Chitungwiza', 'Seke-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_DTvGCun.csv'),
(35, '524401', 'Chitungwiza', 'Seke-Category 1', 2928000000, 0, 0, 0, 2928000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_ivqsfPn.csv'),
(36, '524401', 'Chitungwiza', 'Seke-Category 2', 4488000000, 0, 0, 0, 4488000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_py0KiET.csv'),
(37, '524401', 'Chitungwiza', 'Seke-Major Distribution Maintenace Equipment', 4713430656, 0, 0, 0, 4713430656, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Oa47E8q.csv'),
(38, '524401', 'Chitungwiza', 'District Office -Motor  vehicle', 240250000, 0, 0, 0, 240250000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_71pCTE8.csv'),
(39, '524401', 'Chitungwiza', 'District Office- computers', 194333420, 40000000, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_rj5EoCV.csv'),
(40, '524401', 'Chitungwiza', 'District Office -office &furniture', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_LFuAP9r.csv'),
(41, '524501', 'Warren Park', 'Warren Park -T&E', 409978072.1, 0, 33000000, 0, 376978072.1, '2024-01-15', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_uSzYqjY.csv'),
(42, '524501', 'Warren Park', 'Warren Park -computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_73vLVtu.csv'),
(43, '524501', 'Warren Park', 'Warren Park -office &equipment', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Ob5A9KW.csv'),
(44, '524501', 'Warren Park', 'Warren Park-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_dm928u9.csv'),
(45, '524501', 'Warren Park', 'Warren Park-Category 1', 8745600000, 0, 0, 0, 8745600000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_x9NzIVv.csv'),
(46, '524501', 'Warren Park', 'Warren Park-Category 2', 5755680000, 0, 0, 0, 5755680000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_7oqd9yI.csv'),
(47, '524501', 'Warren Park', 'Warren Park-Major Distribution Maintenace Equipment', 3949777280, 0, 0, 0, 3949777280, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Bbf2lsd.csv'),
(48, '524501', 'Kuwadzana', 'Kuwadzana-T&E', 409978072.1, 0, 123500000, 0, 286478072.1, '2024-01-15', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Dwa2jgm.csv'),
(49, '524501', 'Kuwadzana', 'Kuwadzana -computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_xUe9I9c.csv'),
(50, '524501', 'Kuwadzana', 'Kuwadzana-office &furniture equp', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_ptN3o9H.csv'),
(51, '524501', 'Kuwadzana', 'Kuwadzana-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_C0FGWTg.csv'),
(52, '524501', 'Kuwadzana', 'Kuwadzana-Category 1', 32544000000, 0, 0, 0, 32544000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_ZJ3HgN4.csv'),
(53, '524501', 'Kuwadzana', 'Kuwadzana-Category 2', 12131382036, 0, 0, 0, 12131382036, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_0xUwGy4.csv'),
(54, '524501', 'Kuwadzana', 'Kuwadzana-Major Distribution Maintenace Equipment', 3949777280, 0, 0, 0, 3949777280, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_QGK6n1I.csv'),
(55, '524501', 'Mabelreign', 'Mabelreign-T&E', 409978072.1, 0, 123500000, 0, 286478072.1, '2024-01-15', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_wHC96cq.csv'),
(56, '524501', 'Mabelreign', 'Mabelreign -computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_gg8ctfC.csv'),
(57, '524501', 'Mabelreign', 'Mabelreign -office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_7K8Mq8Z.csv'),
(58, '524501', 'Mabelreign', 'Mabelreign-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_0XCUGce.csv'),
(59, '524501', 'Mabelreign', 'Mabelreign-Category 1', 2880000000, 0, 0, 0, 2880000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_rdmzQOY.csv'),
(60, '524501', 'Mabelreign', 'Mabelreign-Category 2', 3700800000, 0, 0, 0, 3700800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_31HCrit.csv'),
(61, '524501', 'Mabelreign', 'Mabelreign-Major Distribution Maintenace Equipment', 3949777280, 0, 0, 0, 3949777280, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_zUi0fAq.csv'),
(62, '524601', 'Southerton', 'Southerton-T&E', 409978072.1, 70000000, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_MRq1Bwx.csv'),
(63, '524601', 'Southerton', 'Southerton-computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_CSg938Z.csv'),
(64, '524601', 'Southerton', 'Southerton-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_yE4XUSO.csv'),
(65, '524601', 'Southerton', 'Southerton-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Gtyz8Fc.csv'),
(66, '524601', 'Southerton', 'Southerton-Category 2', 6432000000, 0, 0, 0, 6432000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_C6P7gbB.csv'),
(67, '524601', 'Southerton', 'Southerton-Major Distribution Maintenace Equipment', 4951139360, 0, 0, 0, 4951139360, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_5KDNtEH.csv'),
(68, '524601', 'Glen View', 'Glen View-T&E', 409978072.1, 109000000, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_QaYWIfa.csv'),
(69, '524601', 'Glen View', 'Glen View-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_iXAghgA.csv'),
(70, '524601', 'Glen View', 'Glen View -office &furniture equip', 206105670, 28000000, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_KdakKsY.csv'),
(71, '524601', 'Glen View', 'Glen View-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_2u9FAK1.csv'),
(72, '524601', 'Glen View', 'Glen View-Category 1', 5184000000, 0, 0, 0, 5184000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_8AkiMG7.csv'),
(73, '524601', 'Glen View', 'Glen View-Category 2', 27568800000, 0, 0, 0, 27568800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_CwLfAkO.csv'),
(74, '524601', 'Glen View', 'Glen View-Major Distribution Maintenace Equipment', 4951139360, 0, 0, 0, 4951139360, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_iwRgBTP.csv'),
(75, '524601', 'Waterfalls', 'Waterfalls- T&E', 409978072.1, 176000000, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_whquUqi.csv'),
(76, '524601', 'Waterfalls', 'Waterfalls-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_HLYNFJA.csv'),
(77, '524601', 'Waterfalls', 'Waterfalls-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_SyzcCxb.csv'),
(78, '524601', 'Waterfalls', 'Waterfalls-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_9p9rX0p.csv'),
(79, '524601', 'Waterfalls', 'Waterfalls-Category 1', 2016000000, 0, 0, 0, 2016000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_cIP8q6I.csv'),
(80, '524601', 'Waterfalls', 'Waterfalls-Category 2', 37906996800, 0, 0, 0, 37906996800, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_YYMktI2.csv'),
(81, '524601', 'Waterfalls', 'Waterfalls-Major Distribution Maintenace Equipment', 4951139360, 0, 0, 0, 4951139360, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_KzYIyw4.csv'),
(82, '524701', 'Borrowdale', 'Borrowdale-T&E', 409978072.1, 0, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_AEoCRqb.csv'),
(83, '524701', 'Borrowdale', 'Borrowdale-computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Ype99YK.csv'),
(84, '524701', 'Borrowdale', 'Borrowdale-office and equipments', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_qE8oC7l.csv'),
(85, '524701', 'Borrowdale', 'Borrowdale-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_XLdgDC3.csv'),
(86, '524701', 'Borrowdale', 'Borrowdale-Category 1', 4162428160, 0, 0, 0, 4162428160, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Ep8Ix8Z.csv'),
(87, '524701', 'Borrowdale', 'Borrowdale-Category 2', 32463222592, 0, 0, 0, 32463222592, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_zIGkbCR.csv'),
(88, '524701', 'Borrowdale', 'Borrowdale-Major Distribution Maintenace Equipment', 3782776800, 0, 0, 0, 3782776800, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_UVgGWTX.csv'),
(89, '524701', 'CBD', 'CBD-T&E', 409978072.1, 0, 169990000, 0, 239988072.1, '2024-01-17', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_zPGixIs.csv'),
(90, '524701', 'CBD', 'CBD-computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_AwZP30X.csv'),
(91, '524701', 'CBD', 'CBD-office and equipments', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_OwVYhG7.csv'),
(92, '524701', 'CBD', 'CBD-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_D6SZ1rU.csv'),
(93, '524701', 'CBD', 'CBD-Category 1', 3312000000, 0, 0, 0, 3312000000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_NOyJY83.csv'),
(94, '524701', 'CBD', 'CBD-Category 2', 11052800000, 0, 0, 0, 11052800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Xo5RvjU.csv'),
(95, '524701', 'CBD', 'CBD-Major Distribution Maintenace Equipment', 3782776800, 0, 0, 0, 3782776800, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_ktAx05E.csv'),
(96, '524701', 'Mabvuku', 'Mabvuku -T&E', 409978072.1, 0, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_sIrryIi.csv'),
(97, '524701', 'Mabvuku', 'Mabvuku -computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_g3eSgT1.csv'),
(98, '524701', 'Mabvuku', 'Mabvuku -office &equipment', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_TzsQeqo.csv'),
(99, '524701', 'Mabvuku', 'Mabvuku-motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_pFCgIlt.csv'),
(100, '524701', 'Mabvuku', 'Mabvuku-Category 1', 518769600, 0, 0, 0, 518769600, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_EHAISi9.csv'),
(101, '524701', 'Mabvuku', 'Mabvuku-Category 2', 13379520000, 0, 0, 0, 13379520000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_fvMVoap.csv'),
(102, '524701', 'Mabvuku', 'Mabvuku-Major Distribution Maintenace Equipment', 3782776800, 0, 0, 0, 3782776800, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_IsK9Lbg.csv'),
(103, '524701', 'Ruwa', 'Ruwa -T&E', 409978072.1, 0, 0, 0, 409978072.1, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_pBJOTNv.csv'),
(104, '524701', 'Ruwa', 'Ruwa -computers', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_YbfndP0.csv'),
(105, '524701', 'Ruwa', 'Ruwa -office &equipment', 206105670, 1500000, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_HWRW6Q5.csv'),
(106, '524701', 'Ruwa', 'Ruwa -motor vehicles', 1729800000, 0, 0, 0, 1729800000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_4k2NSCq.csv'),
(107, '524701', 'Ruwa', 'Ruwa -Category 1', 77698277568, 0, 0, 0, 77698277568, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_0T43HlM.csv'),
(108, '524701', 'Ruwa', 'Ruwa -Category 2', 32813939808, 0, 0, 0, 32813939808, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_pAHgdc8.csv'),
(109, '524701', 'Ruwa', 'Ruwa -Major Distribution Maintenace Equipment', 3782776800, 0, 0, 0, 3782776800, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_K7FT1B0.csv'),
(110, '525000', 'Commercial', 'Commercial- T&E', 127548725, 0, 0, 0, 127548725, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_T1bqBGn.csv'),
(111, '525000', 'Commercial', 'Commercial-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_ExS0lmf.csv'),
(112, '525000', 'Commercial', 'Commercial-office &furniture equip', 206105670, 27000000, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_oI8wba8.csv'),
(113, '525000', 'Commercial', 'Commercial-motor vehicles', 720750000, 0, 0, 0, 720750000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_50QaJ4u.csv'),
(114, '526001', 'Risk', 'Risk-computer', 194333420, 5000000, 14999999.99, 0, 179333420, '2024-01-17', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_HOQhktr.csv'),
(115, '526001', 'Risk', 'Risk-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_AXCtej5.csv'),
(116, '526001', 'Risk', 'Risk-motor vehicles', 480500000, 0, 0, 0, 480500000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_hdMh6Rw.csv'),
(117, '526001', 'Risk', 'Risk-Category 3', 17600000000, 0, 0, 0, 17600000000, '2024-01-15', 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_8qYwTf5.csv'),
(118, '527001', 'IT', 'IT- T&E', 127548725, 0, 0, 0, 127548725, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_87RAwIV.csv'),
(119, '527001', 'IT', 'IT-computer', 194333420, 0, 0, 0, 194333420, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_CW9p2D5.csv'),
(120, '527001', 'IT', 'IT-office &furniture equip', 206105670, 0, 0, 0, 206105670, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_Us47Fdl.csv'),
(121, '527001', 'IT', 'IT-motor vehicles', 480500000, 0, 0, 0, 480500000, NULL, 2024, 'harare', '2024-02-28', 'uploads/budget/budget_1_rqL20Ib.csv');

-- --------------------------------------------------------

--
-- Table structure for table `ace_transactions`
--

DROP TABLE IF EXISTS `ace_transactions`;
CREATE TABLE IF NOT EXISTS `ace_transactions` (
  `details_of_expenditure` varchar(120) DEFAULT NULL,
  `approval_status` varchar(120) DEFAULT NULL,
  `transaction_id` int(11) NOT NULL AUTO_INCREMENT,
  `region` varchar(120) DEFAULT NULL,
  `amount` double DEFAULT NULL,
  `ace2` varchar(120) DEFAULT NULL,
  `Ace_id2_id` int(11) NOT NULL,
  `budget_id` int(11) NOT NULL,
  PRIMARY KEY (`transaction_id`),
  KEY `Ace_transactions_Ace_id2_id_8c6367be` (`Ace_id2_id`),
  KEY `Ace_transactions_budget_id_4dc39529` (`budget_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `ace_transactions`
--

INSERT INTO `ace_transactions` (`details_of_expenditure`, `approval_status`, `transaction_id`, `region`, `amount`, `ace2`, `Ace_id2_id`, `budget_id`) VALUES
('Testing', 'created', 1, 'Harare', 10, 'ACE2024022886', 1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_group_id_b120cbf9` (`group_id`),
  KEY `auth_group_permissions_permission_id_84c5c92e` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id_2f476e4b` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=169 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add content type', 4, 'add_contenttype'),
(14, 'Can change content type', 4, 'change_contenttype'),
(15, 'Can delete content type', 4, 'delete_contenttype'),
(16, 'Can view content type', 4, 'view_contenttype'),
(17, 'Can add session', 5, 'add_session'),
(18, 'Can change session', 5, 'change_session'),
(19, 'Can delete session', 5, 'delete_session'),
(20, 'Can view session', 5, 'view_session'),
(21, 'Can add nonconformity', 6, 'add_nonconformity'),
(22, 'Can change nonconformity', 6, 'change_nonconformity'),
(23, 'Can delete nonconformity', 6, 'delete_nonconformity'),
(24, 'Can view nonconformity', 6, 'view_nonconformity'),
(25, 'Can add response', 7, 'add_response'),
(26, 'Can change response', 7, 'change_response'),
(27, 'Can delete response', 7, 'delete_response'),
(28, 'Can view response', 7, 'view_response'),
(29, 'Can add user profile', 8, 'add_userprofile'),
(30, 'Can change user profile', 8, 'change_userprofile'),
(31, 'Can delete user profile', 8, 'delete_userprofile'),
(32, 'Can view user profile', 8, 'view_userprofile'),
(33, 'Can add depots', 9, 'add_depots'),
(34, 'Can change depots', 9, 'change_depots'),
(35, 'Can delete depots', 9, 'delete_depots'),
(36, 'Can view depots', 9, 'view_depots'),
(37, 'Can add designations', 10, 'add_designations'),
(38, 'Can change designations', 10, 'change_designations'),
(39, 'Can delete designations', 10, 'delete_designations'),
(40, 'Can view designations', 10, 'view_designations'),
(41, 'Can add districts', 11, 'add_districts'),
(42, 'Can change districts', 11, 'change_districts'),
(43, 'Can delete districts', 11, 'delete_districts'),
(44, 'Can view districts', 11, 'view_districts'),
(45, 'Can add regions', 12, 'add_regions'),
(46, 'Can change regions', 12, 'change_regions'),
(47, 'Can delete regions', 12, 'delete_regions'),
(48, 'Can view regions', 12, 'view_regions'),
(49, 'Can add roles', 13, 'add_roles'),
(50, 'Can change roles', 13, 'change_roles'),
(51, 'Can delete roles', 13, 'delete_roles'),
(52, 'Can view roles', 13, 'view_roles'),
(53, 'Can add sections', 14, 'add_sections'),
(54, 'Can change sections', 14, 'change_sections'),
(55, 'Can delete sections', 14, 'delete_sections'),
(56, 'Can view sections', 14, 'view_sections'),
(57, 'Can add notification', 15, 'add_notification'),
(58, 'Can change notification', 15, 'change_notification'),
(59, 'Can delete notification', 15, 'delete_notification'),
(60, 'Can view notification', 15, 'view_notification'),
(61, 'Can add file', 16, 'add_file'),
(62, 'Can change file', 16, 'change_file'),
(63, 'Can delete file', 16, 'delete_file'),
(64, 'Can view file', 16, 'view_file'),
(65, 'Can add inspections', 17, 'add_inspections'),
(66, 'Can change inspections', 17, 'change_inspections'),
(67, 'Can delete inspections', 17, 'delete_inspections'),
(68, 'Can view inspections', 17, 'view_inspections'),
(69, 'Can add maintenance', 18, 'add_maintenance'),
(70, 'Can change maintenance', 18, 'change_maintenance'),
(71, 'Can delete maintenance', 18, 'delete_maintenance'),
(72, 'Can view maintenance', 18, 'view_maintenance'),
(73, 'Can add pbnc', 19, 'add_pbnc'),
(74, 'Can change pbnc', 19, 'change_pbnc'),
(75, 'Can delete pbnc', 19, 'delete_pbnc'),
(76, 'Can view pbnc', 19, 'view_pbnc'),
(77, 'Can add td', 20, 'add_td'),
(78, 'Can change td', 20, 'change_td'),
(79, 'Can delete td', 20, 'delete_td'),
(80, 'Can view td', 20, 'view_td'),
(81, 'Can add upo', 21, 'add_upo'),
(82, 'Can change upo', 21, 'change_upo'),
(83, 'Can delete upo', 21, 'delete_upo'),
(84, 'Can view upo', 21, 'view_upo'),
(85, 'Can add categories', 22, 'add_categories'),
(86, 'Can change categories', 22, 'change_categories'),
(87, 'Can delete categories', 22, 'delete_categories'),
(88, 'Can view categories', 22, 'view_categories'),
(89, 'Can add filetype', 23, 'add_filetype'),
(90, 'Can change filetype', 23, 'change_filetype'),
(91, 'Can delete filetype', 23, 'delete_filetype'),
(92, 'Can view filetype', 23, 'view_filetype'),
(93, 'Can add first_ category', 24, 'add_first_category'),
(94, 'Can change first_ category', 24, 'change_first_category'),
(95, 'Can delete first_ category', 24, 'delete_first_category'),
(96, 'Can view first_ category', 24, 'view_first_category'),
(97, 'Can add knowledge center', 25, 'add_knowledgecenter'),
(98, 'Can change knowledge center', 25, 'change_knowledgecenter'),
(99, 'Can delete knowledge center', 25, 'delete_knowledgecenter'),
(100, 'Can view knowledge center', 25, 'view_knowledgecenter'),
(101, 'Can add secondary_ category', 26, 'add_secondary_category'),
(102, 'Can change secondary_ category', 26, 'change_secondary_category'),
(103, 'Can delete secondary_ category', 26, 'delete_secondary_category'),
(104, 'Can view secondary_ category', 26, 'view_secondary_category'),
(105, 'Can add departments', 27, 'add_departments'),
(106, 'Can change departments', 27, 'change_departments'),
(107, 'Can delete departments', 27, 'delete_departments'),
(108, 'Can view departments', 27, 'view_departments'),
(109, 'Can add work instr', 28, 'add_workinstr'),
(110, 'Can change work instr', 28, 'change_workinstr'),
(111, 'Can delete work instr', 28, 'delete_workinstr'),
(112, 'Can view work instr', 28, 'view_workinstr'),
(113, 'Can add departments', 29, 'add_departments'),
(114, 'Can change departments', 29, 'change_departments'),
(115, 'Can delete departments', 29, 'delete_departments'),
(116, 'Can view departments', 29, 'view_departments'),
(117, 'Can add risk files', 30, 'add_riskfiles'),
(118, 'Can change risk files', 30, 'change_riskfiles'),
(119, 'Can delete risk files', 30, 'delete_riskfiles'),
(120, 'Can view risk files', 30, 'view_riskfiles'),
(121, 'Can add ace', 31, 'add_ace'),
(122, 'Can change ace', 31, 'change_ace'),
(123, 'Can delete ace', 31, 'delete_ace'),
(124, 'Can view ace', 31, 'view_ace'),
(125, 'Can add budget', 32, 'add_budget'),
(126, 'Can change budget', 32, 'change_budget'),
(127, 'Can delete budget', 32, 'delete_budget'),
(128, 'Can view budget', 32, 'view_budget'),
(129, 'Can add transactions', 33, 'add_transactions'),
(130, 'Can change transactions', 33, 'change_transactions'),
(131, 'Can delete transactions', 33, 'delete_transactions'),
(132, 'Can view transactions', 33, 'view_transactions'),
(133, 'Can add procurement', 34, 'add_rfq'),
(134, 'Can change procurement', 34, 'change_rfq'),
(135, 'Can delete procurement', 34, 'delete_rfq'),
(136, 'Can view procurement', 34, 'view_rfq'),
(137, 'Can add meter token', 35, 'add_metertoken'),
(138, 'Can change meter token', 35, 'change_metertoken'),
(139, 'Can delete meter token', 35, 'delete_metertoken'),
(140, 'Can view meter token', 35, 'view_metertoken'),
(141, 'Can add organisational charts', 36, 'add_organisationalcharts'),
(142, 'Can change organisational charts', 36, 'change_organisationalcharts'),
(143, 'Can delete organisational charts', 36, 'delete_organisationalcharts'),
(144, 'Can view organisational charts', 36, 'view_organisationalcharts'),
(145, 'Can add application', 37, 'add_application'),
(146, 'Can change application', 37, 'change_application'),
(147, 'Can delete application', 37, 'delete_application'),
(148, 'Can view application', 37, 'view_application'),
(149, 'Can add workflow', 38, 'add_workflow'),
(150, 'Can change workflow', 38, 'change_workflow'),
(151, 'Can delete workflow', 38, 'delete_workflow'),
(152, 'Can view workflow', 38, 'view_workflow'),
(153, 'Can add role', 39, 'add_role'),
(154, 'Can change role', 39, 'change_role'),
(155, 'Can delete role', 39, 'delete_role'),
(156, 'Can view role', 39, 'view_role'),
(157, 'Can add step', 40, 'add_step'),
(158, 'Can change step', 40, 'change_step'),
(159, 'Can delete step', 40, 'delete_step'),
(160, 'Can view step', 40, 'view_step'),
(161, 'Can add approval', 41, 'add_approval'),
(162, 'Can change approval', 41, 'change_approval'),
(163, 'Can delete approval', 41, 'delete_approval'),
(164, 'Can view approval', 41, 'view_approval'),
(165, 'Can add quotation', 42, 'add_quotation'),
(166, 'Can change quotation', 42, 'change_quotation'),
(167, 'Can delete quotation', 42, 'delete_quotation'),
(168, 'Can view quotation', 42, 'view_quotation');

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=43 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(2, 'auth', 'permission'),
(3, 'auth', 'group'),
(4, 'contenttypes', 'contenttype'),
(5, 'sessions', 'session'),
(6, 'nonconformity', 'nonconformity'),
(7, 'nonconformity', 'response'),
(8, 'users', 'userprofile'),
(9, 'users', 'depots'),
(10, 'users', 'designations'),
(11, 'users', 'districts'),
(12, 'users', 'regions'),
(13, 'users', 'roles'),
(14, 'users', 'sections'),
(15, 'users', 'notification'),
(16, 'exec_dashboards', 'file'),
(17, 'exec_dashboards', 'inspections'),
(18, 'exec_dashboards', 'maintenance'),
(19, 'exec_dashboards', 'pbnc'),
(20, 'exec_dashboards', 'td'),
(21, 'exec_dashboards', 'upo'),
(22, 'knowledge_center', 'categories'),
(23, 'knowledge_center', 'filetype'),
(24, 'knowledge_center', 'first_category'),
(25, 'knowledge_center', 'knowledgecenter'),
(26, 'knowledge_center', 'secondary_category'),
(27, 'processes', 'departments'),
(28, 'processes', 'workinstr'),
(29, 'process_risks', 'departments'),
(30, 'process_risks', 'riskfiles'),
(31, 'Ace', 'ace'),
(32, 'Ace', 'budget'),
(33, 'Ace', 'transactions'),
(34, 'procurement', 'procurement'),
(35, 'tempertockens', 'metertoken'),
(36, 'competence_building', 'organisationalcharts'),
(37, 'approve', 'application'),
(38, 'approve', 'workflow'),
(39, 'approve', 'role'),
(40, 'approve', 'step'),
(41, 'approve', 'approval'),
(42, 'procurement', 'quotation');

-- --------------------------------------------------------

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=28 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'users', '0001_initial', '2024-02-28 08:14:47.095102'),
(2, 'users', '0002_remove_userprofile_roles_userprofile_roles', '2024-02-28 08:26:05.607207'),
(3, 'Ace', '0001_initial', '2024-02-28 08:29:31.966081'),
(4, 'contenttypes', '0001_initial', '2024-02-28 08:29:31.988531'),
(5, 'admin', '0001_initial', '2024-02-28 08:29:32.053239'),
(6, 'admin', '0002_logentry_remove_auto_add', '2024-02-28 08:29:32.064305'),
(7, 'admin', '0003_logentry_add_action_flag_choices', '2024-02-28 08:29:32.074341'),
(8, 'contenttypes', '0002_remove_content_type_name', '2024-02-28 08:29:32.118326'),
(9, 'auth', '0001_initial', '2024-02-28 08:29:32.240658'),
(10, 'auth', '0002_alter_permission_name_max_length', '2024-02-28 08:29:32.262778'),
(11, 'auth', '0003_alter_user_email_max_length', '2024-02-28 08:29:32.274149'),
(12, 'auth', '0004_alter_user_username_opts', '2024-02-28 08:29:32.287650'),
(13, 'auth', '0005_alter_user_last_login_null', '2024-02-28 08:29:32.333137'),
(14, 'auth', '0006_require_contenttypes_0002', '2024-02-28 08:29:32.337760'),
(15, 'auth', '0007_alter_validators_add_error_messages', '2024-02-28 08:29:32.348481'),
(16, 'auth', '0008_alter_user_username_max_length', '2024-02-28 08:29:32.356596'),
(17, 'auth', '0009_alter_user_last_name_max_length', '2024-02-28 08:29:32.367200'),
(18, 'auth', '0010_alter_group_name_max_length', '2024-02-28 08:29:32.388966'),
(19, 'auth', '0011_update_proxy_permissions', '2024-02-28 08:29:32.415049'),
(20, 'auth', '0012_alter_user_first_name_max_length', '2024-02-28 08:29:32.426303'),
(21, 'exec_dashboards', '0001_initial', '2024-02-28 08:29:32.484064'),
(22, 'knowledge_center', '0001_initial', '2024-02-28 08:29:32.597400'),
(23, 'nonconformity', '0001_initial', '2024-02-28 08:29:32.735226'),
(24, 'sessions', '0001_initial', '2024-02-28 08:29:32.760515'),
(25, 'users', '0003_userprofile_groups_userprofile_is_superuser_and_more', '2024-02-28 08:43:44.232955'),
(26, 'Ace', '0002_alter_ace_gm_approval_status', '2024-02-28 10:25:33.492482'),
(27, 'procurement', '0001_initial', '2024-03-04 07:25:43.590472');

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('h4mp030412migc3j2g51n67opilwq6uw', '.eJxVjEEOwiAQRe_C2hA60AIu3XsGMsNMpWpoUtqV8e7apAvd_vfef6mE21rS1mRJE6uz6tTpdyPMD6k74DvW26zzXNdlIr0r-qBNX2eW5-Vw_w4KtvKtHZONGXm0FAMRkJU8APbGgM8jRHDO92IDisMYBIHEd2Ag0mDFsVHvD_0qOCM:1rfK9U:v2lMMaa0_bbpIgbQaDfnWYPlpbQYutulOzKAgDn1NMA', '2024-03-13 13:39:16.632896'),
('6w3m1ly2xo62nctm63lg6ysd5g98cuaj', '.eJxVjEEOwiAQRe_C2hCBMoBL956BDMMgVUOT0q6MdzckXej2v_f-W0Tctxr3zmucs7gIL06_W0J6chsgP7DdF0lL29Y5yaHIg3Z5WzK_rof7d1Cx11ETTJiKc8oTIiAAYyLOirUKhDmQdoZVUcoaY6eSwHIA7azPWM5gxOcLGUE4lg:1rfb98:6FyRPyQZ3tL1ydiOF_0oHacdxWRCMxIvsqFqaJT3aj4', '2024-03-14 07:48:02.817804'),
('uszt22sk04dn0cik0fl82cc9pt77s4b8', '.eJxVjEEOwiAQRe_C2hA60AIu3XsGMsNMpWpoUtqV8e7apAvd_vfef6mE21rS1mRJE6uz6tTpdyPMD6k74DvW26zzXNdlIr0r-qBNX2eW5-Vw_w4KtvKtHZONGXm0FAMRkJU8APbGgM8jRHDO92IDisMYBIHEd2Ag0mDFsVHvD_0qOCM:1rfyRO:HNOSAj85ZnW84MzUhG05f1joMALJ0UYQfZe2Sqw9yCk', '2024-03-15 08:40:26.568463'),
('4cvivzrrm5snixsm0co9lgmfs0h3sfr6', '.eJxVjMsOwiAUBf-FtSF4KdC6dO83EO4DqRqalHZl_HfbpAvdnpk5bxXTupS4NpnjyOqiQJ1-N0z0lLoDfqR6nzRNdZlH1LuiD9r0bWJ5XQ_376CkVrbagCX2bIwTHggtmC7j0ImxkF1vAYMnYIM-2ERJPAn0wfF5c7NH9urzBeRTOFM:1rh2W8:os5nJykq1aHgUFHpsGKD4qETstjCqBUc1HsVGFVyDwA', '2024-03-18 07:13:44.145917');

-- --------------------------------------------------------

--
-- Table structure for table `exec_dashboards_file`
--

DROP TABLE IF EXISTS `exec_dashboards_file`;
CREATE TABLE IF NOT EXISTS `exec_dashboards_file` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `file` varchar(100) NOT NULL,
  `name` varchar(255) NOT NULL,
  `file_type` varchar(50) NOT NULL,
  `content` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `exec_dashboards_inspections`
--

DROP TABLE IF EXISTS `exec_dashboards_inspections`;
CREATE TABLE IF NOT EXISTS `exec_dashboards_inspections` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `location` varchar(100) DEFAULT NULL,
  `depot` varchar(100) DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `created_at` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `exec_dashboards_maintenance`
--

DROP TABLE IF EXISTS `exec_dashboards_maintenance`;
CREATE TABLE IF NOT EXISTS `exec_dashboards_maintenance` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `location` varchar(100) DEFAULT NULL,
  `depot` varchar(100) DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `created_at` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `exec_dashboards_pbnc`
--

DROP TABLE IF EXISTS `exec_dashboards_pbnc`;
CREATE TABLE IF NOT EXISTS `exec_dashboards_pbnc` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `reciept_no` varchar(150) DEFAULT NULL,
  `ics_ref` varchar(150) DEFAULT NULL,
  `ndm_ref` varchar(150) DEFAULT NULL,
  `name` varchar(80) DEFAULT NULL,
  `address` varchar(150) DEFAULT NULL,
  `capacity` varchar(100) DEFAULT NULL,
  `project_type` varchar(50) DEFAULT NULL,
  `amount` varchar(50) DEFAULT NULL,
  `depot` varchar(100) DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `payment_date` date DEFAULT NULL,
  `created_at` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `exec_dashboards_td`
--

DROP TABLE IF EXISTS `exec_dashboards_td`;
CREATE TABLE IF NOT EXISTS `exec_dashboards_td` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `amount` varchar(50) DEFAULT NULL,
  `depot` varchar(100) DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `created_at` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `exec_dashboards_upo`
--

DROP TABLE IF EXISTS `exec_dashboards_upo`;
CREATE TABLE IF NOT EXISTS `exec_dashboards_upo` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `description` varchar(80) DEFAULT NULL,
  `depot` varchar(100) DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `created_at` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `knowledge_center_categories`
--

DROP TABLE IF EXISTS `knowledge_center_categories`;
CREATE TABLE IF NOT EXISTS `knowledge_center_categories` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `file_type` varchar(100) NOT NULL,
  `cat_1` varchar(100) NOT NULL,
  `cat_2` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `knowledge_center_filetype`
--

DROP TABLE IF EXISTS `knowledge_center_filetype`;
CREATE TABLE IF NOT EXISTS `knowledge_center_filetype` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `knowledge_center_first_category`
--

DROP TABLE IF EXISTS `knowledge_center_first_category`;
CREATE TABLE IF NOT EXISTS `knowledge_center_first_category` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `file_type_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `knowledge_center_first_category_file_type_id_c20d3eb1` (`file_type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `knowledge_center_knowledgecenter`
--

DROP TABLE IF EXISTS `knowledge_center_knowledgecenter`;
CREATE TABLE IF NOT EXISTS `knowledge_center_knowledgecenter` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `filename` varchar(100) NOT NULL,
  `file_type` varchar(100) NOT NULL,
  `sub_category_1` varchar(100) NOT NULL,
  `sub_category_2` varchar(100) NOT NULL,
  `filepath` varchar(400) NOT NULL,
  `section` varchar(100) NOT NULL,
  `region` varchar(100) NOT NULL,
  `created_at` date NOT NULL,
  `updated_at` date NOT NULL,
  `created_by` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `knowledge_center_secondary_category`
--

DROP TABLE IF EXISTS `knowledge_center_secondary_category`;
CREATE TABLE IF NOT EXISTS `knowledge_center_secondary_category` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `category_id` bigint(20) NOT NULL,
  `file_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `knowledge_center_secondary_category_category_id_cd82b80c` (`category_id`),
  KEY `knowledge_center_secondary_category_file_id_68cf4529` (`file_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `nonconformity_nonconformity`
--

DROP TABLE IF EXISTS `nonconformity_nonconformity`;
CREATE TABLE IF NOT EXISTS `nonconformity_nonconformity` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `description` longtext,
  `root_cause` longtext,
  `violation_standard_reference` varchar(400) DEFAULT NULL,
  `recommended_corrective_action` varchar(300) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `attachment` varchar(100) DEFAULT NULL,
  `plan_of_action` longtext,
  `expected_completion_date` date DEFAULT NULL,
  `created_by_id` bigint(20) NOT NULL,
  `recipient_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `nonconformity_nonconformity_created_by_id_8ef750fc` (`created_by_id`),
  KEY `nonconformity_nonconformity_recipient_id_1a782c9d` (`recipient_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `nonconformity_nonconformity`
--

INSERT INTO `nonconformity_nonconformity` (`id`, `description`, `root_cause`, `violation_standard_reference`, `recommended_corrective_action`, `created_at`, `attachment`, `plan_of_action`, `expected_completion_date`, `created_by_id`, `recipient_id`) VALUES
(1, 'test', 'cause', 'violation', 'action', '2024-02-28 10:59:30.182880', 'static/nonconformity_files/Companies_Act_Chapter_24-03_updated.pdf', NULL, NULL, 1, 2),
(2, 'testing 2', 'cause 3', 'standard', 'actions', '2024-02-28 11:00:21.309815', '', NULL, NULL, 1, 2),
(3, 'Them', 'dsfdg', 'dsdf', 'dsgh', '2024-02-28 14:40:25.942160', 'nonconformity_attachments/Screenshot_2023-12-17_143122.png', NULL, NULL, 1, 4);

-- --------------------------------------------------------

--
-- Table structure for table `nonconformity_response`
--

DROP TABLE IF EXISTS `nonconformity_response`;
CREATE TABLE IF NOT EXISTS `nonconformity_response` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `comment` longtext,
  `created_at` datetime(6) NOT NULL,
  `status` varchar(20) NOT NULL,
  `nonconformity_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `nonconformity_response_nonconformity_id_a88d66bc` (`nonconformity_id`),
  KEY `nonconformity_response_user_id_e03856ad` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `quotation`
--

DROP TABLE IF EXISTS `quotation`;
CREATE TABLE IF NOT EXISTS `quotation` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `quotation_file` varchar(100) NOT NULL,
  `rfq_id` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `quotation_rfq_id_74409d41` (`rfq_id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `quotation`
--

INSERT INTO `quotation` (`id`, `quotation_file`, `rfq_id`) VALUES
(1, 'uploads/procurement/20240304023411PMrequirements.txt', 'RFQ2024030495'),
(2, 'uploads/procurement/20240304023411PMrequirements.txt', 'RFQ2024030495'),
(3, 'uploads/procurement/20240304023411PMrequirements.txt', 'RFQ2024030495'),
(4, 'uploads/procurement/20240304023801PMLICENSE', 'RFQ2024030418');

-- --------------------------------------------------------

--
-- Table structure for table `procurement`
--

DROP TABLE IF EXISTS `procurement`;
CREATE TABLE IF NOT EXISTS `procurement` (
  `rfq_id` varchar(20) NOT NULL,
  `rfq_type` varchar(15) DEFAULT NULL,
  `allocation_code_of_expenditure` varchar(100) DEFAULT NULL,
  `scope_of_work` varchar(100) DEFAULT NULL,
  `quantity` double DEFAULT NULL,
  `proc_ref` varchar(100) DEFAULT NULL,
  `amount` double DEFAULT NULL,
  `payment_mode` varchar(100) DEFAULT NULL,
  `requested_by` varchar(100) DEFAULT NULL,
  `section_code` varchar(100) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `date_created` date DEFAULT NULL,
  `approval_status` varchar(120) DEFAULT NULL,
  `date_approved` date DEFAULT NULL,
  `section_head` varchar(100) DEFAULT NULL,
  `finance_manager` varchar(100) DEFAULT NULL,
  `general_manager` varchar(100) DEFAULT NULL,
  `general_manager_approval_status` varchar(100) DEFAULT NULL,
  `general_manager_approval_date` date DEFAULT NULL,
  `general_manager_rejection_reason` longtext,
  `finance_manager_approval_status` varchar(100) DEFAULT NULL,
  `finance_manager_approval_date` date DEFAULT NULL,
  `finance_manager_rejection_reason` longtext,
  `section_head_approval_status` varchar(100) DEFAULT NULL,
  `section_head_approval_date` date DEFAULT NULL,
  `section_head_rejection_reason` longtext,
  `ace_id2` int(11) DEFAULT NULL,
  PRIMARY KEY (`rfq_id`),
  KEY `rfq_ace_id2_bf87af07` (`ace_id2`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `procurement`
--

INSERT INTO `procurement` (`rfq_id`, `rfq_type`, `allocation_code_of_expenditure`, `scope_of_work`, `quantity`, `proc_ref`, `amount`, `payment_mode`, `requested_by`, `section_code`, `designation`, `date_created`, `approval_status`, `date_approved`, `section_head`, `finance_manager`, `general_manager`, `general_manager_approval_status`, `general_manager_approval_date`, `general_manager_rejection_reason`, `finance_manager_approval_status`, `finance_manager_approval_date`, `finance_manager_rejection_reason`, `section_head_approval_status`, `section_head_approval_date`, `section_head_rejection_reason`, `ace_id2`) VALUES
('RFQ2024030421', 'Non-Ace', '2993', ' LIQUID SANITIZER FOR COVID PREVENTIONS TACTICS', 120, '234', 100, 'ecocash', 'testing2', '527001', '15', '2024-03-04', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
('RFQ2024030495', 'Non-Ace', '2993', ' LIQUID SANITIZER FOR COVID PREVENTIONS TACTICS', 120, '234', 100, 'ecocash', 'testing2', '527001', '15', '2024-03-04', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
('RFQ2024030418', 'Non-Ace', '299', ' LIQUID SANITIZER FOR COVID PREVENTIONS TACTICS', 120, '234', 100, 'ecocash', 'testing2', '527001', '15', '2024-03-04', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

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

-- --------------------------------------------------------

--
-- Table structure for table `users_districts`
--

DROP TABLE IF EXISTS `users_districts`;
CREATE TABLE IF NOT EXISTS `users_districts` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `district` varchar(100) NOT NULL,
  `code` varchar(100) NOT NULL,
  `region_id` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_districts`
--

INSERT INTO `users_districts` (`id`, `district`, `code`, `region_id`) VALUES
(1, 'Chitungwiza District', '524401', '1'),
(2, 'North District', '524501', '1'),
(3, 'South District', '524601', '1'),
(4, 'East District', '524701', '1');

-- --------------------------------------------------------

--
-- Table structure for table `users_notification`
--

DROP TABLE IF EXISTS `users_notification`;
CREATE TABLE IF NOT EXISTS `users_notification` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `url` varchar(250) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_notification_user_id_fed360c8` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_notification`
--

INSERT INTO `users_notification` (`id`, `message`, `created_at`, `is_read`, `url`, `user_id`) VALUES
(1, 'nc: test', '2024-02-28 10:59:30.185883', 0, '/nonconformity/1/', 2),
(2, 'nc: testing 2', '2024-02-28 11:00:21.310813', 0, '/nonconformity/2/', 2),
(3, 'nc: Them', '2024-02-28 14:40:25.945153', 0, '/nonconformity/3/', 4);

-- --------------------------------------------------------

--
-- Table structure for table `users_regions`
--

DROP TABLE IF EXISTS `users_regions`;
CREATE TABLE IF NOT EXISTS `users_regions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `region` varchar(100) NOT NULL,
  `code` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_regions`
--

INSERT INTO `users_regions` (`id`, `region`, `code`) VALUES
(1, 'Harare', ''),
(2, 'East', ''),
(3, 'South', ''),
(4, 'West', '');

-- --------------------------------------------------------

--
-- Table structure for table `users_roles`
--

DROP TABLE IF EXISTS `users_roles`;
CREATE TABLE IF NOT EXISTS `users_roles` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role` varchar(100) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(400) NOT NULL,
  `application` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=47 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_roles`
--

INSERT INTO `users_roles` (`id`, `role`, `name`, `description`, `application`) VALUES
(5, 'originator', 'Auditor', 'Role for the Auditor', 'non_conformity'),
(4, 'pay', 'Payer', 'Confirms the payment', 'remittance_advice'),
(3, 'authorise', 'Authoriser', 'Authorises the Remiitance Advice for Payment', 'remittance_advice'),
(2, 'check', 'Checker', 'Checks the Prepared Remittance Advice', 'remittance_advice'),
(1, 'prepare', 'Requester', 'Creates the Remittance advice Note', 'remittance_advice'),
(6, 'recipient', 'Recipient', 'Role for the recipeint of the Non Conformity', 'non_conformity'),
(7, 'supervisor', 'Section Head/ Customer Services Officer', 'Normally the Section Head responsible for checking on the progress on NC raised on their subordinates', 'non_conformity'),
(8, 'create', 'Requester', 'Petty Cash Requester', 'pettycash'),
(9, 'approve', 'Section Head / Customer Services Officer', 'Section Head/ Supervisor', 'pettycash'),
(10, 'disburse', 'Cashier', 'Role for disburing pettycash', 'pettycash'),
(11, 'create', 'Requester', 'Direct purchases requester', 'adjudication'),
(12, 'check', 'Foreperson/ Customer Services Officer', 'Foreperson role for Checking a direct purchases request', 'adjudication'),
(13, 'process', 'Procurement Officer', 'Role for Procurement Officer', 'adjudication'),
(14, 'approve', 'Section Head/ District Manager', 'Role for Section Head or District Manager', 'adjudication'),
(15, 'confirm', 'Finance Manager', 'Finance Manager Role', 'adjudication'),
(16, 'authorise', 'General Manager', 'General Manager role for Authorisation', 'adjudication'),
(17, 'create', 'Requester', 'Role for token Requester', 'tokens'),
(18, 'approve', 'Section Head', 'Role for token approver', 'tokens'),
(19, 'generation', 'Revenue Officer', 'Role for Revenue Officer responsible for Token Generation', 'tokens'),
(20, 'meter downloading', 'Meter Downloading (Engineer)', 'Role for Engineer responsible for meter downloading', 'tokens'),
(21, 'stores', 'Stores Officer', 'Role for Stores Officer for Reimbursement Tokens', 'tokens'),
(22, 'create', 'Procurement Officer', 'Role for Procurement Officer responsible for creating tender documents', 'tenders'),
(23, 'check', 'Finance Manager', 'Role for Finance Manager', 'tenders'),
(24, 'approve', 'General Manager', 'Role for General Manager', 'tenders'),
(25, 'request', 'Requester', 'Role for Procurement requester', 'tenders'),
(26, 'verify', 'Foreperson/ Customer Services Officer', 'Role for the CSO/Foreperson for verifying Procurement requests', 'tenders'),
(27, 'authorise', 'Section Head/ District Manager', 'Role for Section Head/ District Manager for Authorising Procurement requests', 'tenders'),
(28, 'create', 'Requester', 'Role for ACE requester', 'ace'),
(29, 'check', 'Foreperson/ Customer Services Officer', 'Role for CSO/Foreperson for checking ACE request', 'ace'),
(30, 'pass', 'Section Head/ District Manager', 'Role for Section Head or District Manager', 'ace'),
(31, 'process', 'Accounting Officer', 'Role for Accounting Officer resposible for generating and attaching asset numbers to ACE`s.', 'ace'),
(32, 'sanction', 'Finance Manager', 'Role for Finance Manager', 'ace'),
(33, 'approve', 'General Manager', 'Role for General Manager', 'ace'),
(34, 'order', 'Procurement Officer', 'Role for Procurement Officer', 'ace'),
(35, 'authoriser', 'Petty Cash Authoriser', 'Petty Cash Authoriser', 'pettycash'),
(36, 'create', 'Requester', 'appraisal Requester', 'appraisal'),
(37, 'approve', 'Section Head', 'Section Head', 'appraisal'),
(38, 'reviewer', 'reviewer', 'Role for reviewing appraisal', 'appraisal'),
(39, 'hr', 'hr', 'Role for hr in appraisal', 'appraisal'),
(40, 'admin', 'Administrator', 'IT Administrator', 'users'),
(41, 'standard', 'Standard', 'Standard User', 'users'),
(42, 'create', 'Procurement Officer', 'Role for Procurement Officer responsible for creating Procurement documents', 'procurement'),
(43, 'check', 'Finance Manager', 'Role for Finance Manager', 'procurement'),
(44, 'approve', 'General Manager', 'Role for General Manager', 'procurement'),
(45, 'request', 'Requester', 'Role for Procurement requester', 'procurement'),
(46, 'authenticate', 'Section head', 'Role for Procurement Section head', 'procurement');

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

-- --------------------------------------------------------

--
-- Table structure for table `users_userprofile`
--

DROP TABLE IF EXISTS `users_userprofile`;
CREATE TABLE IF NOT EXISTS `users_userprofile` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `username` varchar(15) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `status` varchar(30) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `last_reset` date NOT NULL,
  `depot_id` bigint(20) DEFAULT NULL,
  `designation_id` bigint(20) DEFAULT NULL,
  `district_id` bigint(20) DEFAULT NULL,
  `region_id` bigint(20) DEFAULT NULL,
  `section_id` bigint(20) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `users_userprofile_depot_id_2b017c9f` (`depot_id`),
  KEY `users_userprofile_designation_id_6261b042` (`designation_id`),
  KEY `users_userprofile_district_id_df58cc98` (`district_id`),
  KEY `users_userprofile_region_id_d47e029c` (`region_id`),
  KEY `users_userprofile_section_id_3044c8a6` (`section_id`)
) ENGINE=MyISAM AUTO_INCREMENT=9 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_userprofile`
--

INSERT INTO `users_userprofile` (`id`, `password`, `last_login`, `username`, `first_name`, `last_name`, `email`, `status`, `is_staff`, `is_active`, `date_joined`, `last_reset`, `depot_id`, `designation_id`, `district_id`, `region_id`, `section_id`, `is_superuser`) VALUES
(1, 'pbkdf2_sha256$390000$yHWKqhxFcvkDpao5DcRrK7$a+WnnCVtYGLxFhOsb3t+xTYK45eind5zh6yY4cEL7ss=', '2024-03-01 09:45:34.873913', '12345', 'Test', 'User', 'testuser@email.com', '', 1, 1, '2024-02-28 08:36:09.337362', '2024-02-28', NULL, 132, NULL, 1, 12, 0),
(2, 'pbkdf2_sha256$390000$BuP2giqRkmDeZLumpbAjNh$LzYR3e+nkMAFktQHNk0G+qAM+58ac0FDk32vCzMAsQ8=', '2024-03-01 09:53:08.865519', 'testing2', 'Test2', 'User2', 'testuser@email.com', 'active', 0, 1, '2024-02-28 10:58:52.963673', '2024-02-28', NULL, 15, NULL, 1, 12, 0),
(3, 'pbkdf2_sha256$390000$L8Lk6WjjQrlfAuVMtU9gsU$LPonZy+6NkKKxFhSaZ1+HnuBCFgrd4YkHklxYcQHj0M=', '2024-03-01 09:49:10.899453', 'test3', 'Test3', 'User', 'test3user@email.com', 'active', 0, 1, '2024-02-28 11:27:20.957738', '2024-02-28', NULL, 15, NULL, 1, 12, 0),
(4, 'Password123', NULL, 't4', 'Test4', 'User', 'testudser@email.com', 'active', 0, 1, '2024-02-28 11:36:11.387214', '2024-02-28', NULL, 16, NULL, 1, 1, 0),
(5, 'Password123', NULL, 'test5', 'T5', 'User', 'testuser5@email.com', 'active', 0, 1, '2024-02-28 12:53:55.266730', '2024-02-28', NULL, 57, NULL, 1, 9, 0),
(6, '', NULL, 'test6', 'Test6', 'User', 'testuser6@email.com', 'active', 0, 1, '2024-02-29 05:00:58.269204', '2024-02-29', NULL, 15, NULL, 1, 10, 0),
(7, '', NULL, 'testing7', 'Test7', 'User', 'testing7@user.com', 'active', 0, 1, '2024-02-29 05:03:34.132151', '2024-02-29', NULL, 65, NULL, 1, 11, 0),
(8, 'pbkdf2_sha256$390000$GW66csvNjq548iiEqxPj8S$fu40ujNajDvPmhHaBpH5ACEjn6u0uwaXRU67WzGDOTo=', '2024-03-01 09:51:15.099290', 'test7', 'test7', 'User', 'testuser7@email.com', 'active', 0, 1, '2024-02-29 07:47:21.327851', '2024-02-29', NULL, 59, NULL, 1, 1, 0);

-- --------------------------------------------------------

--
-- Table structure for table `users_userprofile_groups`
--

DROP TABLE IF EXISTS `users_userprofile_groups`;
CREATE TABLE IF NOT EXISTS `users_userprofile_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `userprofile_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_userprofile_groups_userprofile_id_group_id_823cf2fc_uniq` (`userprofile_id`,`group_id`),
  KEY `users_userprofile_groups_userprofile_id_a4496a80` (`userprofile_id`),
  KEY `users_userprofile_groups_group_id_3de53dbf` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `users_userprofile_roles`
--

DROP TABLE IF EXISTS `users_userprofile_roles`;
CREATE TABLE IF NOT EXISTS `users_userprofile_roles` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `userprofile_id` bigint(20) NOT NULL,
  `roles_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_userprofile_roles_userprofile_id_roles_id_c30d0711_uniq` (`userprofile_id`,`roles_id`),
  KEY `users_userprofile_roles_userprofile_id_ae49de2a` (`userprofile_id`),
  KEY `users_userprofile_roles_roles_id_de9f6492` (`roles_id`)
) ENGINE=MyISAM AUTO_INCREMENT=57 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users_userprofile_roles`
--

INSERT INTO `users_userprofile_roles` (`id`, `userprofile_id`, `roles_id`) VALUES
(34, 5, 40),
(33, 5, 8),
(32, 5, 6),
(31, 5, 4),
(30, 2, 31),
(29, 1, 20),
(28, 1, 13),
(27, 1, 9),
(26, 1, 40),
(25, 1, 6),
(24, 1, 24),
(23, 1, 3),
(22, 1, 28),
(14, 2, 4),
(15, 2, 8),
(16, 2, 22),
(17, 2, 19),
(18, 2, 29),
(19, 2, 6),
(20, 2, 40),
(21, 2, 13),
(35, 5, 11),
(36, 5, 17),
(37, 5, 25),
(38, 5, 28),
(39, 7, 4),
(40, 7, 6),
(41, 7, 8),
(42, 7, 40),
(43, 7, 11),
(44, 7, 17),
(45, 7, 22),
(46, 7, 28),
(47, 8, 4),
(48, 8, 5),
(49, 8, 8),
(50, 8, 40),
(51, 8, 11),
(52, 8, 17),
(53, 8, 22),
(54, 8, 28),
(55, 2, 42),
(56, 1, 45);

-- --------------------------------------------------------

--
-- Table structure for table `users_userprofile_user_permissions`
--

DROP TABLE IF EXISTS `users_userprofile_user_permissions`;
CREATE TABLE IF NOT EXISTS `users_userprofile_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `userprofile_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_userprofile_user_p_userprofile_id_permissio_d0215190_uniq` (`userprofile_id`,`permission_id`),
  KEY `users_userprofile_user_permissions_userprofile_id_34544737` (`userprofile_id`),
  KEY `users_userprofile_user_permissions_permission_id_393136b6` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
