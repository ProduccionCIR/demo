-- COREHUB DEMO / RAV SYSTEM
-- Ejecutar SOLO en una base PostgreSQL/Supabase NUEVA y dedicada a demo.
-- Requiere public.clientes y public.productos según las migraciones compatibles.
-- Datos de ejemplo totalmente ficticios; correos de example.com.
-- No crea usuarios ni credenciales inseguras.
BEGIN;
DO $$
BEGIN
 IF to_regclass('public.clientes') IS NULL OR to_regclass('public.productos') IS NULL THEN
  RAISE EXCEPTION 'Faltan las tablas clientes/productos: aplicar migraciones del proyecto primero.';
 END IF;
 IF EXISTS (SELECT 1 FROM public.clientes LIMIT 1) OR EXISTS (SELECT 1 FROM public.productos LIMIT 1) THEN
  RAISE EXCEPTION 'Semilla cancelada: se exige clientes y productos vacíos. No sobrescribir datos.';
 END IF;
END $$;
INSERT INTO public.clientes (nombre,identificacion,telefono,direccion,email,registrado_por,es_offshore,tipo_cliente,pais,ciudad,limite_credito,saldo_pendiente)
VALUES
 ('Distribuidora Horizonte DEMO','DEMO-RUC-001','000-0001','Dirección ficticia, Colón','horizonte@example.com','demo',false,'NACIONAL','Panamá','Colón',10000,0),
 ('Comercial Pacífico DEMO','DEMO-RUC-002','000-0002','Dirección ficticia, Panamá','pacifico@example.com','demo',false,'NACIONAL','Panamá','Panamá',15000,0),
 ('Importadora Caribe DEMO','DEMO-RUC-003','000-0003','Dirección ficticia, San José','caribe@example.com','demo',true,'INTERNACIONAL','Costa Rica','San José',20000,0),
 ('Servicios Atlántico DEMO','DEMO-RUC-004','000-0004','Dirección ficticia, David','atlantico@example.com','demo',false,'NACIONAL','Panamá','David',5000,0);
INSERT INTO public.productos (referencia,descripcion,marca,tipo,cantidad,u_m,costo_unit,precio,total,cantidad_caja,galera,pasillo,rack,nivel,stock_minimo,origen_pais)
VALUES
 ('DEMO-001','Filtro industrial demostración','GENÉRICA DEMO','Repuestos',120,'UNIDAD',8.50,15.00,1020,12,'A','P01','R01','N1',15,'Panamá'),
 ('DEMO-002','Lubricante sintético demostración','GENÉRICA DEMO','Lubricantes',64,'UNIDAD',19.00,32.00,1216,6,'A','P01','R02','N1',10,'Panamá'),
 ('DEMO-003','Kit de herramientas demostración','GENÉRICA DEMO','Herramientas',42,'UNIDAD',35.00,59.00,1470,4,'B','P02','R01','N1',5,'Panamá'),
 ('DEMO-004','Caja de suministros demostración','GENÉRICA DEMO','Suministros',80,'CAJA',11.00,20.00,880,1,'B','P02','R03','N2',12,'Panamá'),
 ('DEMO-005','Sensor digital demostración','GENÉRICA DEMO','Electrónica',95,'UNIDAD',14.00,27.00,1330,10,'A','P03','R04','N1',20,'Panamá');
COMMIT;
