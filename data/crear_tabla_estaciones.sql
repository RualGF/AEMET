CREATE TABLE `estaciones` (
  `codigo_indicativo` varchar(10) COLLATE utf8mb4_es_0900_ai_ci NOT NULL,
  `nombre_estacion` varchar(100) COLLATE utf8mb4_es_0900_ai_ci NOT NULL,
  `codigo_prov` tinyint unsigned NOT NULL,
  `cluster` tinyint unsigned NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `latitud_dd` float DEFAULT NULL,
  `longitud_dd` float DEFAULT NULL,
  PRIMARY KEY (`codigo_indicativo`),
  UNIQUE KEY `codigo_indicativo_UNIQUE` (`codigo_indicativo`),
  KEY `codigo_prov` (`codigo_prov`),
  CONSTRAINT `estaciones_ibfk_1` FOREIGN KEY (`codigo_prov`) REFERENCES `provincias` (`codigo_prov`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_es_0900_ai_ci