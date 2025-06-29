CREATE TABLE `comunidades` (
  `codigo_ca` tinyint unsigned NOT NULL,
  `nombre_ccaa` varchar(50) COLLATE utf8mb4_es_0900_ai_ci NOT NULL,
  PRIMARY KEY (`codigo_ca`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_es_0900_ai_ci

INSERT INTO comunidades(codigo_ca, nombre) VALUES
('01', 'Andalucía'),
('02', 'Aragón'),
('03', 'Illes Balears'),
('04', 'Canarias'),
('05', 'Cantabria'),
('06', 'Castilla - La Mancha'),
('07', 'Castilla y León'),
('08', 'Cataluña'),
('09', 'Ceuta'),
('10', 'Extremadura'),
('11', 'Galicia'),
('12', 'La Rioja'),
('13', 'Madrid, Comunidad de'),
('14', 'Melilla'),
('15', 'Murcia, Región de'),
('16', 'Navarra, Comunidad Foral de'),
('17', 'País Vasco'),
('18', 'Principado de Asturias'),
('19', 'Comunitat Valenciana');

select * from comunidades ;