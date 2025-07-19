-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Schema mydb

DROP SCHEMA IF EXISTS `mydb`;

CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8;
USE `mydb`;


-- Table `mydb`.`rol`


CREATE TABLE IF NOT EXISTS `mydb`.`rol` (
`idRol` INT NOT NULL,
`name` VARCHAR(45) NOT NULL DEFAULT 'asd',
PRIMARY KEY (`idRol`)
) ENGINE = InnoDB;

-- Table `mydb`.`user`


CREATE TABLE IF NOT EXISTS `mydb`.`user` (
`username` VARCHAR(16) NOT NULL,
`password` VARCHAR(256) NOT NULL,
`mac` VARCHAR(45) NULL,
`table1_idRol` INT NOT NULL,
`nombre` VARCHAR(100) NOT NULL,
PRIMARY KEY (`username`),
INDEX `fk_user_table1_idx` (`table1_idRol` ASC),
CONSTRAINT `fk_user_table1`
FOREIGN KEY (`table1_idRol`)
REFERENCES `mydb`.`rol` (`idRol`)
ON DELETE NO ACTION
ON UPDATE NO ACTION
) ENGINE = InnoDB;


-- Table `mydb`.`regla`

CREATE TABLE IF NOT EXISTS `mydb`.`regla` (
`id` INT NOT NULL,
`nameRule` VARCHAR(45) NOT NULL,
`regla` VARCHAR(500) NOT NULL,
`ip_src` VARCHAR(45) NOT NULL,
`ip_dst` VARCHAR(45) NOT NULL,
PRIMARY KEY (`id`)
) ENGINE = InnoDB;

-- Table `mydb`.`rol_has_regla`


CREATE TABLE IF NOT EXISTS `mydb`.`rol_has_regla` (
`rol_idRol` INT NOT NULL,
`regla_id` INT NOT NULL,
PRIMARY KEY (`rol_idRol`, `regla_id`),
INDEX `fk_rol_has_regla_regla1_idx` (`regla_id` ASC),
INDEX `fk_rol_has_regla_rol1_idx` (`rol_idRol` ASC),
CONSTRAINT `fk_rol_has_regla_rol1`
FOREIGN KEY (`rol_idRol`)
REFERENCES `mydb`.`rol` (`idRol`)
ON DELETE NO ACTION
ON UPDATE NO ACTION,
CONSTRAINT `fk_rol_has_regla_regla1`
FOREIGN KEY (`regla_id`)
REFERENCES `mydb`.`regla` (`id`)
ON DELETE NO ACTION
ON UPDATE NO ACTION
) ENGINE = InnoDB;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;


-- Data for table `mydb`.`rol`



START TRANSACTION;
USE `mydb`;
INSERT INTO `mydb`.`rol` (`idRol`, `name`) VALUES
(1, 'ESTDIANTE\_LETRAS'),
(2, 'ESTDIANTE\_CIENCIAS'),
(3, 'ESTDIANTE\_DERECHO'),
(4, 'ESTUDIANTE\_TELECOM'),
(5, 'ADMINISTRATIVO\_DTI'),
(6, 'EXTERNO');
COMMIT;


-- Data for table `mydb`.`user`


START TRANSACTION;
USE `mydb`;
INSERT INTO `mydb`.`user` (`username`, `password`, `mac`, `table1_idRol`, `nombre`) VALUES
('20190001', 'clave1', NULL, 1, 'Mar Tomatodo'),
('20190002', 'clave2', NULL, 2, 'Apple Fino'),
('20190003', 'clave3', NULL, 3, 'Sofia Comepan'),
('20190004', 'clave4', NULL, 4, 'Alejandro Cerveron'),
('20190005', 'clave5', NULL, 5, 'Ricardu Carranza'),
('20190006', 'clave6', NULL, 6, 'Jorge Luna');
COMMIT;


-- Data for table `mydb`.`regla`



START TRANSACTION;
USE `mydb`;
INSERT INTO `mydb`.`regla` (`id`,`nameRule`,`regla`,`ip_src`,`ip_dst`) VALUES
(1,  'ARP2i',  '{"eth_type":"0x806","arp_spa":"10.0.0.1","arp_tpa":"10.0.0.2"}',                          '10.0.0.1','10.0.0.2'),
(2,  'ARP2v',  '{"eth_type":"0x806","arp_spa":"10.0.0.2","arp_tpa":"10.0.0.1"}',                          '10.0.0.1','10.0.0.2'),
(3,  'FTP2i',  '{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"21","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.2"}', '10.0.0.1','10.0.0.2'),
(4,  'FTP2v',  '{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"21","ipv4_src":"10.0.0.2","ipv4_dst":"10.0.0.1"}', '10.0.0.1','10.0.0.2'),
(5,  'ICMP2i','{"eth_type":"0x800","ip_proto":"1","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.2"}',          '10.0.0.1','10.0.0.2'),
(6,  'ICMP2v','{"eth_type":"0x800","ip_proto":"1","ipv4_src":"10.0.0.2","ipv4_dst":"10.0.0.1"}',          '10.0.0.1','10.0.0.2'),
(7,  'SSH2i', '{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"22","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.2"}', '10.0.0.1','10.0.0.2'),
(8,  'SSH2v', '{"eth_type":"0x0800","ip_proto":"6","tcp_src":"22","ipv4_src":"10.0.0.2","ipv4_dst":"10.0.0.1"}', '10.0.0.1','10.0.0.2'),
(9,  'HTTP2i','{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"80","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.2"}', '10.0.0.1','10.0.0.2'),
(10, 'HTTP2v','{"eth_type":"0x0800","ip_proto":"6","tcp_src":"80","ipv4_src":"10.0.0.2","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.2'),
(11, 'DNS2i', '{"eth_type":"0x0800","ip_proto":"17","udp_dst":"53","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.2"}','10.0.0.1','10.0.0.2'),
(12, 'DNS2v', '{"eth_type":"0x0800","ip_proto":"17","udp_src":"53","ipv4_src":"10.0.0.2","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.2'),
(13, 'HTTPS2i','{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"443","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.2"}','10.0.0.1','10.0.0.2'),
(14, 'HTTPS2v','{"eth_type":"0x0800","ip_proto":"6","tcp_src":"443","ipv4_src":"10.0.0.2","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.2'),
(15, 'FTP3i', '{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"21","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.3"}','10.0.0.1','10.0.0.3'),
(16, 'FTP3v', '{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"21","ipv4_src":"10.0.0.3","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.3'),
(17, 'SSH3i', '{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"22","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.3"}','10.0.0.1','10.0.0.3'),
(18, 'SSH3v', '{"eth_type":"0x0800","ip_proto":"6","tcp_src":"22","ipv4_src":"10.0.0.3","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.3'),
(19, 'HTTP3i','{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"80","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.3"}','10.0.0.1','10.0.0.3'),
(20, 'HTTP3v','{"eth_type":"0x0800","ip_proto":"6","tcp_src":"80","ipv4_src":"10.0.0.3","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.3'),
(21, 'DNS3i', '{"eth_type":"0x0800","ip_proto":"17","udp_dst":"53","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.3"}','10.0.0.1','10.0.0.3'),
(22, 'DNS3v', '{"eth_type":"0x0800","ip_proto":"17","udp_src":"53","ipv4_src":"10.0.0.3","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.3'),
(23, 'HTTPS3i','{"eth_type":"0x0800","ip_proto":"6","tcp_dst":"443","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.3"}','10.0.0.1','10.0.0.3'),
(24, 'HTTPS3v','{"eth_type":"0x0800","ip_proto":"6","tcp_src":"443","ipv4_src":"10.0.0.3","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.3'),
(25, 'ARP3i', '{"eth_type":"0x806","arp_spa":"10.0.0.1","arp_tpa":"10.0.0.3"}','10.0.0.1','10.0.0.3'),
(26, 'ARP3v', '{"eth_type":"0x806","arp_spa":"10.0.0.3","arp_tpa":"10.0.0.1"}','10.0.0.1','10.0.0.3'),
(27, 'ICMP3i','{"eth_type":"0x800","ip_proto":"1","ipv4_src":"10.0.0.1","ipv4_dst":"10.0.0.3"}','10.0.0.1','10.0.0.3'),
(28, 'ICMP3v','{"eth_type":"0x800","ip_proto":"1","ipv4_src":"10.0.0.3","ipv4_dst":"10.0.0.1"}','10.0.0.1','10.0.0.3');


COMMIT;

-- Data for table `mydb`.`rol_has_regla`


START TRANSACTION;
USE `mydb`;
INSERT INTO `mydb`.`rol_has_regla` (`rol_idRol`, `regla_id`) VALUES
(1, 19),(1, 20),(1, 25),(1, 26),
(2, 19),(2, 20),(2, 25),(2, 26),(2, 1),(2, 2),(2, 3),(2, 4),
(3, 19),(3, 20),(3, 25),(3, 26),(3, 15),(3, 16),(1, 15),(1, 16),
(4, 1),(4, 2),(4, 25),(4, 26),(4, 5),(4, 6),(4, 27),(4, 28),(4, 17),(4, 18),
(6, 25),(6, 26),(6, 19),(6, 20),
(5, 1),(5, 2),(5, 7),(5, 8),(5, 9),(5, 10),(5, 5),(5, 6);
COMMIT;
