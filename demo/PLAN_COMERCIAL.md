# Presentación comercial de CoreHub DEMO

## Guion práctico (15-20 minutos)
1. Dashboard: explicar indicadores y periodo.
2. Clientes: registrar cliente **ficticio** en vivo.
3. Inventario: registrar un producto DEMO y localizarlo en WMS.
4. Cotizaciones: preparar cotización para el nuevo cliente.
5. Ventas: convertir a proforma/factura demo; explicar inventario.
6. Caja y CxC: emitir recibo demo; mostrar saldo.
7. Contabilidad y reportes: visualizar trazabilidad y exportación, tras validar integración.
8. Cierre: mostrar opciones de implementación y mensualidades sin comprometer funciones no verificadas.

## Seguridad y privacidad
- Borrar datos que el prospecto pudiera ingresar por error (nombres, teléfonos, correos reales).
- Usar watermark **DEMO - DOCUMENTO SIN VALIDEZ FISCAL** en impresiones.
- Eliminar/restablecer datos solo desde una acción autenticada y auditable.
- Captura de leads comercial separada de datos transaccionales ficticios.
- La demo no es ambiente contable certificado ni sistema de facturación fiscal.

## Criterio de aceptación
Navegar, crear, editar y consultar registros reales de la base demo desde navegador y que persistan entre sesiones. La operación debe funcionar después de una redeploy en Render, y nunca compartir credenciales o base con producción.
