-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: consultorio_rc
-- ------------------------------------------------------
-- Server version	8.4.6

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `dentista_dentista`
--

DROP TABLE IF EXISTS `dentista_dentista`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dentista_dentista` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `especialidad` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `licencia` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `foto_perfil` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `dentista_dentista_user_id_191896b6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dentista_dentista`
--

LOCK TABLES `dentista_dentista` WRITE;
/*!40000 ALTER TABLE `dentista_dentista` DISABLE KEYS */;
INSERT INTO `dentista_dentista` VALUES (1,'diego','3220000000','Cirujano Dentista',NULL,'',1),(2,'Rodolfo','3220000000','Cirujano Dentista',NULL,'',3);
/*!40000 ALTER TABLE `dentista_dentista` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dentista_servicio`
--

DROP TABLE IF EXISTS `dentista_servicio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dentista_servicio` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  `duracion_estimada` int NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `dentista_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dentista_servicio_dentista_id_101c12db_fk_dentista_dentista_id` (`dentista_id`),
  CONSTRAINT `dentista_servicio_dentista_id_101c12db_fk_dentista_dentista_id` FOREIGN KEY (`dentista_id`) REFERENCES `dentista_dentista` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dentista_servicio`
--

LOCK TABLES `dentista_servicio` WRITE;
/*!40000 ALTER TABLE `dentista_servicio` DISABLE KEYS */;
/*!40000 ALTER TABLE `dentista_servicio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dentista_cita`
--

DROP TABLE IF EXISTS `dentista_cita`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dentista_cita` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `hora_inicio` time(6) NOT NULL,
  `hora_fin` time(6) NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notas` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `archivo_adjunto` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `dentista_id` bigint NOT NULL,
  `paciente_id` bigint NOT NULL,
  `servicio_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dentista_cita_servicio_id_d69bf613_fk_dentista_servicio_id` (`servicio_id`),
  KEY `dentista_cita_dentista_id_30f39219_fk_dentista_dentista_id` (`dentista_id`),
  KEY `dentista_cita_paciente_id_3010e8b1_fk_dentista_paciente_id` (`paciente_id`),
  CONSTRAINT `dentista_cita_dentista_id_30f39219_fk_dentista_dentista_id` FOREIGN KEY (`dentista_id`) REFERENCES `dentista_dentista` (`id`),
  CONSTRAINT `dentista_cita_paciente_id_3010e8b1_fk_dentista_paciente_id` FOREIGN KEY (`paciente_id`) REFERENCES `dentista_paciente` (`id`),
  CONSTRAINT `dentista_cita_servicio_id_d69bf613_fk_dentista_servicio_id` FOREIGN KEY (`servicio_id`) REFERENCES `dentista_servicio` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dentista_cita`
--

LOCK TABLES `dentista_cita` WRITE;
/*!40000 ALTER TABLE `dentista_cita` DISABLE KEYS */;
/*!40000 ALTER TABLE `dentista_cita` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dentista_paciente`
--

DROP TABLE IF EXISTS `dentista_paciente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dentista_paciente` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direccion` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `antecedentes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `dentista_id` bigint NOT NULL,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `dentista_paciente_dentista_id_e284508f_fk_dentista_dentista_id` (`dentista_id`),
  CONSTRAINT `dentista_paciente_dentista_id_e284508f_fk_dentista_dentista_id` FOREIGN KEY (`dentista_id`) REFERENCES `dentista_dentista` (`id`),
  CONSTRAINT `dentista_paciente_user_id_d30291dc_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dentista_paciente`
--

LOCK TABLES `dentista_paciente` WRITE;
/*!40000 ALTER TABLE `dentista_paciente` DISABLE KEYS */;
INSERT INTO `dentista_paciente` VALUES (1,'David Aceves Lepe','1111111111','',NULL,'','2025-11-28 00:43:49.871623',2,NULL);
/*!40000 ALTER TABLE `dentista_paciente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dentista_pago`
--

DROP TABLE IF EXISTS `dentista_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dentista_pago` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `monto` decimal(10,2) NOT NULL,
  `metodo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `cita_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cita_id` (`cita_id`),
  CONSTRAINT `dentista_pago_cita_id_2f596eb4_fk_dentista_cita_id` FOREIGN KEY (`cita_id`) REFERENCES `dentista_cita` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dentista_pago`
--

LOCK TABLES `dentista_pago` WRITE;
/*!40000 ALTER TABLE `dentista_pago` DISABLE KEYS */;
/*!40000 ALTER TABLE `dentista_pago` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dentista_horario`
--

DROP TABLE IF EXISTS `dentista_horario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dentista_horario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `dia_semana` int NOT NULL,
  `hora_inicio` time(6) NOT NULL,
  `hora_fin` time(6) NOT NULL,
  `dentista_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dentista_horario_dentista_id_4f4073e0_fk_dentista_dentista_id` (`dentista_id`),
  CONSTRAINT `dentista_horario_dentista_id_4f4073e0_fk_dentista_dentista_id` FOREIGN KEY (`dentista_id`) REFERENCES `dentista_dentista` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dentista_horario`
--

LOCK TABLES `dentista_horario` WRITE;
/*!40000 ALTER TABLE `dentista_horario` DISABLE KEYS */;
/*!40000 ALTER TABLE `dentista_horario` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-03 21:39:09
