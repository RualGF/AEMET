CREATE TABLE datos_meteorologicos (
    fecha DATE NOT NULL,
    indicativo_estacion VARCHAR(10) NOT NULL,
    nombre_estacion VARCHAR(100),
    -- nombre_provincia VARCHAR(50), -- No la guardamos si ya tenemos codigo_provincia
    codigo_provincia SMALLINT UNSIGNED, -- FK a provincias
    altitud SMALLINT UNSIGNED,
    temperatura_media DECIMAL(4,1),
    precipitacion DECIMAL(5,1),
    temperatura_minima DECIMAL(4,1),
    hora_tmin TIME,
    temperatura_maxima DECIMAL(4,1),
    hora_tmax TIME,
    direccion_viento SMALLINT,
    velocidad_media_viento DECIMAL(4,1),
    racha_max_viento DECIMAL(4,1),
    hora_racha TIME,
    humedad_rel_media SMALLINT,
    humedad_rel_max SMALLINT,
    hora_hr_max VARCHAR(10), -- Puede ser 'Varias'
    humedad_rel_min SMALLINT,
    hora_hr_min TIME,
    PRIMARY KEY (fecha, indicativo_estacion), -- Clave primaria compuesta
    FOREIGN KEY (codigo_provincia) REFERENCES provincias(codigo_ine)
);