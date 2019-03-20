-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               10.2.12-MariaDB - mariadb.org binary distribution
-- Server OS:                    Win64
-- HeidiSQL Version:             9.4.0.5125
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- Dumping database structure for boardgamegeek
CREATE DATABASE IF NOT EXISTS `boardgamegeek` /*!40100 DEFAULT CHARACTER SET utf8_unicode_ci */;
USE `boardgamegeek`;

-- Dumping structure for table boardgamegeek.description_word_bigram
CREATE TABLE IF NOT EXISTS `description_word_bigram` (
  `first` varchar(125) COLLATE utf8_unicode_ci NOT NULL,
  `second` varchar(125) COLLATE utf8_unicode_ci NOT NULL,
  `frequency` int(11) NOT NULL,
  PRIMARY KEY (`first`,`second`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- Data exporting was unselected.
-- Dumping structure for table boardgamegeek.game_detail
CREATE TABLE IF NOT EXISTS `game_detail` (
  `id` int(11) NOT NULL,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `description` varchar(12000) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- Data exporting was unselected.
-- Dumping structure for table boardgamegeek.process
CREATE TABLE IF NOT EXISTS `process` (
  `game_id` int(11) NOT NULL,
  `description_word_bigram` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `title_letterpair_bigram` tinyint(1) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`game_id`),
  CONSTRAINT `FK__GAME_ID_DESCRIPTION` FOREIGN KEY (`game_id`) REFERENCES `game_detail` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- Data exporting was unselected.
-- Dumping structure for table boardgamegeek.title_letterpair_bigram
CREATE TABLE IF NOT EXISTS `title_letterpair_bigram` (
  `first` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `second` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `frequency` int(11) NOT NULL,
  PRIMARY KEY (`first`,`second`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- Data exporting was unselected.
-- Dumping structure for view boardgamegeek.status
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `status` (
	`Total known games` BIGINT(21) NULL,
	`Descriptions processed for word bigrams` BIGINT(21) NULL,
	`Total word bigrams` BIGINT(21) NULL,
	`Titles processed for letter pair bigrams` BIGINT(21) NULL,
	`Total letter pair bigrams` BIGINT(21) NULL
) ENGINE=MyISAM;

-- Dumping structure for procedure boardgamegeek.sp_reset_description_word_bigrams
DELIMITER //
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_reset_description_word_bigrams`()
    MODIFIES SQL DATA
    COMMENT 'This will clear the description bigram table and reset the associated bit in the process table. Allows the process to start over. '
BEGIN
delete from description_word_bigram;
update process set description_word_bigram = 0;
END//
DELIMITER ;

-- Dumping structure for procedure boardgamegeek.sp_reset_title_letterpair_bigrams
DELIMITER //
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_reset_title_letterpair_bigrams`()
    MODIFIES SQL DATA
BEGIN
delete from title_letterpair_bigram;
update process set title_letterpair_bigram = 0;
END//
DELIMITER ;

-- Dumping structure for view boardgamegeek.status
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `status`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` VIEW `status` AS select
	(SELECT count(*) from game_detail) as 'Total known games',
	(SELECT count(*) from process where description_word_bigram = 1) as 'Descriptions processed for word bigrams',
	(SELECT count(*) from description_word_bigram) as 'Total word bigrams',
	(SELECT count(*) from process where title_letterpair_bigram = 1) as 'Titles processed for letter pair bigrams',
	(SELECT count(*) from title_letterpair_bigram) as 'Total letter pair bigrams'
from dual ;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
