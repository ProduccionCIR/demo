# Repositorio destino de la demo

Esta carpeta contiene los recursos de preparación de CoreHub DEMO. **Todavía no es una aplicación comercial publicada.** La rama actual conserva el contenido histórico Python del repositorio; la incorporación completa de CoreHub Node.js y las pruebas están pendientes.

⚠️ La rama main contiene archivos `.env`, `secrets.toml` y ficheros de base de datos locales en un repositorio público. Auditar y rotar inmediatamente cualquier secreto real que haya estado versionado, y eliminarlos del repositorio e historial antes del lanzamiento.

# CoreHub DEMO comercial — RAV SYSTEM

Entorno comercial aislado basado en la versión Node.js de CoreHub (rama fuente `deploy/render-db-standard-v1`).

## Estado
Rama de preparación creada. NO desplegada. El archivo SQL incluido contiene ejemplos ficticios compatibles con las tablas básicas de la aplicación. La demo debe usar una base de datos exclusivamente de demostración y una configuración de Render independiente.

## Principios de seguridad
- Nunca conectar esta rama a las bases de RAMGOZL, DANA, InfinityGrafik ni RAV SYSTEM.
- Crear proyecto Supabase/PostgreSQL nuevo para demo; no utilizar bases de producción para pruebas.
- Cargar esquema de migraciones de esta rama en el proyecto nuevo; verificar estructura exacta antes de ejecutar la semilla.
- Ejecutar `demo/seed_demo.sql` SOLO en la base demo vacía, después del esquema. No ejecutarlo en producción.
- Crear usuarios demo de manera segura desde el sistema, con contraseñas aleatorias únicas y permisos mínimos. No usar perfiles predeterminados ni contraseñas de prueba públicas.
- Rotular el sitio y todo PDF generado como DEMOSTRACIÓN / SIN VALIDEZ FISCAL.
- Exponer cuentas de vendedor para demostraciones supervisadas; no permitir acceso Master IT público.
- Separar la configuración de entorno y secretos de cada instancia; nunca enviar service-role keys al navegador.
- Añadir rate limiting, auditoría, restablecimiento seguro, límites de almacenamiento y protección contra datos reales antes de ofrecer acceso público autoservicio.

## Despliegue previsto
- Repo: `ProduccionCIR/demo`.
- Rama: `feature/corehub-demo-node-20261021`.
- Render: servicio web nuevo (NO modificar servicio de RAMGOZL).
- Runtime: Node >=22.
- Build: `npm ci --include=dev && npm run lint && npm run build`.
- Start: `npm start`.
- Health: `/api/health`.
- Variables de entorno: nueva URL y clave pública/anon Supabase DEMO, según configuración documentada en `.env.example` y `render.yaml`.
- Persistencia: proyecto Supabase/PostgreSQL DEMO independiente. Render instancia gratuita, si es elegible, puede suspenderse.

## Estado de funcionalidades
La aplicación base contiene módulos de dashboard, inventario, compras, proformas, ventas, clientes, caja, contabilidad y reportes; las funciones que dependan de tablas/migraciones especiales deben someterse a pruebas funcionales en la base de datos demo. La semilla solo crea registros básicos (clientes/productos); no simula una auditoría contable completa.

## Pruebas imprescindibles para publicar
Login/RBAC, registro de producto y cliente, cotización, emisión de proforma, efecto de inventario, recibos, asientos y reportes; probar persistencia tras reinicio y acceso simultáneo. Ninguna operación puede tocar datos de clientes reales.

## Siguiente paso
Confirmar el espacio de trabajo Render y aprovisionar base exclusivamente demo. Después desplegar servicio separado y validar cada módulo en URL pública.
