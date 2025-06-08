CREATE TABLE datos_meteorologicos (
    id_descarga VARCHAR(50) NOT NULL,
    fecha DATE NOT NULL,
    indicativo_estacion VARCHAR(10) NOT NULL,
    nombre_estacion VARCHAR(100),
    -- nombre_provincia VARCHAR(50), -- No la guardamos si ya tenemos codigo_provincia
    codigo_provincia TINYINT UNSIGNED, -- FK a provincias
    altitud SMALLINT UNSIGNED,
    tmed DECIMAL(4,1),
    tmin DECIMAL(4,1),
    tmax DECIMAL(4,1),
    prec DECIMAL(5,1),
    velmedia DECIMAL(4,1),
    racha DECIMAL(4,1),
    hrMedia SMALLINT,
    timestamp_extraccion DATETIME NOT NULL,
    PRIMARY KEY (fecha, indicativo_estacion), -- Clave primaria compuesta
    FOREIGN KEY (codigo_provincia) REFERENCES provincias(codigo_prov)
);