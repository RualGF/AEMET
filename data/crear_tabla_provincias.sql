CREATE TABLE IF NOT EXISTS provincias (
    codigo_prov TINYINT UNSIGNED PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    codigo_ca TINYINT UNSIGNED NOT NULL,
    FOREIGN KEY (codigo_ca) REFERENCES comunidades(codigo_ca)
);

INSERT INTO provincias (codigo_prov, nombre, codigo_ca) VALUES
('01', 'Araba/Álava', '17'),
('02', 'Albacete', '06'),
('03', 'Alacant/Alicante', '19'),
('04', 'Almería', '01'),
('05', 'Ávila', '07'),
('06', 'Badajoz', '10'),
('07', 'Illes Balears', '03'),
('08', 'Barcelona', '08'),
('09', 'Burgos', '07'),
('10', 'Cáceres', '10'),
('11', 'Cádiz', '01'),
('12', 'Castelló/Castellón', '19'),
('13', 'Ciudad Real', '06'),
('14', 'Córdoba', '01'),
('15', 'A Coruña', '11'),
('16', 'Cuenca', '06'),
('17', 'Girona', '08'),
('18', 'Granada', '01'),
('19', 'Guadalajara', '06'),
('20', 'Gipuzkoa/Guipúzcoa', '17'),
('21', 'Huelva', '01'),
('22', 'Huesca', '02'),
('23', 'Jaén', '01'),
('24', 'León', '07'),
('25', 'Lleida', '08'),
('26', 'La Rioja', '12'),
('27', 'Lugo', '11'),
('28', 'Madrid', '13'),
('29', 'Málaga', '01'),
('30', 'Murcia', '15'),
('31', 'Navarra', '16'),
('32', 'Ourense', '11'),
('33', 'Asturias', '18'),
('34', 'Palencia', '07'),
('35', 'Las Palmas', '04'),
('36', 'Pontevedra', '11'),
('37', 'Salamanca', '07'),
('38', 'Santa Cruz De Tenerife', '04'),
('39', 'Cantabria', '05'),
('40', 'Segovia', '07'),
('41', 'Sevilla', '01'),
('42', 'Soria', '07'),
('43', 'Tarragona', '08'),
('44', 'Teruel', '02'),
('45', 'Toledo', '06'),
('46', 'València/Valencia', '19'),
('47', 'Valladolid', '07'),
('48', 'Bizkaia/Vizcaya', '17'),
('49', 'Zamora', '07'),
('50', 'Zaragoza', '02'),
('51', 'Ceuta', '09'),
('52', 'Melilla', '14');

SELECT
    p.nombre AS provincia,
    c.nombre AS comunidad
FROM
    provincias p
JOIN
    comunidades c ON p.codigo_ca = c.codigo_ca
ORDER BY
    p.nombre;