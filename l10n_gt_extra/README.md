Instalación:
0) pip install pandas (Linux) ó python.exe -m pip install pandas (Windows Server)
1) Ingresar a aplicaciones en modo desarrollador > luego "Actualizar lista de aplicaciones" y Actualizar
2) Buscar la aplicación "Guatemala - Contabilidad Extra" o l10n_gt_extra y hacer clic en "Instalar"

Configuración:
1) Configuración por empresa:
	1.1) Crear cuentas para exención ventas, ISR ventas, retención IVA ventas, ISR compras, IVA compras (Plan de Cuentas)
	1.2) Seleccionar cuentas en configuracion (Ajustes generales > Contabilidad > Retenciones), debemos de seleccionar todas las cuentas creadas en el 1.1
	1.3) Seleccionar usuarios en configuracion (Ajustes generales > Contabilidad > Pagos electronicos), debemos de seleccionar el usuario que da el visto bueno y el encargado de ejecutarlos (Esta configuracion sirve para reporte de solicitud de pagos)
	1.4) Seleccionar diarios a excluir en reportes contables (Ajustes generales > Contabilidad > Reportes Contabilidad) [Aplica para diario, mayor, inventario]
	1.5) Configuracion Libro de ventas (Ajustes generales > Contabilidad > Configuraciones Adicionales Libro de Ventas) > Seleccionar Campo Establecimiento, numero factura y serie factura (campo del diario que indica el establecimiento, campo de la factura que refiere al numero y serie de la factura)
	1.6) Configuracion empresa/contactos > se debera de seleccionar el regimen del isr y del iva > Para cada contacto debera de configurarse una unica vez
	1.7) Configuracion Libro Financiero > (Contabilidad > Configuracion > Contabilidad > Configuracion Reportes GT) > Ingresar toda la configuracion del reporte

Generacion de reportes:
	1) Libro Ventas: Ingresar a Contabilidad > Reportes > Reportes SAT > Libro de Ventas; luego se debera de seleccionar los diarios de los establecimientos, asi como las fechas y los impuestos y por ultimo, hacer clic en Imprimir (Excel o PDF)
	2) Libro Compras: Ingresar a Contabilidad > Reportes > Reportes SAT > Libro de Compras; luego se debera de seleccionar los diarios de los establecimientos, asi como las fechas y el impuesto y por ultimo, hacer clic en Imprimir (Excel o PDF)
	3) Libro Bancos: Ingresar a Contabilidad > Reportes > Reportes SAT > Libro de Banco; luego se debera de seleccionar la cuenta del banco, asi como las fechas y por ultimo, hacer clic en Reporte (PDF)
	4) Libro Inventario: Ingresar a Contabilidad > Reportes > Reportes SAT > Libro inventario; luego se debera de seleccionar las cuentas, asi como las fecha final y por ultimo, hacer clic en Reporte (PDF)
	5) Libro Diario: Ingresar a Contabilidad > Reportes > Reportes SAT > Libro de Diario; luego se debera de seleccionar las cuentas, tipo de agrupacion, asi como el rango de fecha y folio y por ultimo, hacer clic en Reporte (Excel o PDF)
	6) Libro Mayor general: Ingresar a Contabilidad > Reportes > Reportes SAT > Libro mayor general; luego se debera de seleccionar las cuentas, tipo de agrupacion, asi como el rango de fecha y folio y por ultimo, hacer clic en Reporte (Excel o PDF)
	7) Libro Financiero: Ingresar a Contabilidad > Reportes > Reportes SAT > Libro Financiero; luego se debera de seleccionar el tipo de reporte, asi como el rango de fecha y folio y por ultimo, hacer clic en Reporte (PDF)
	8) Reporte de Cheques: Ingresar a Contabilidad > Reportes > Reporte de Cheques; luego seleccionar fechas y diario de la cuenta y hacer clic en Reporte (Excel)
	9) Reporte de Partida: Ingresar a Contabilidad > Asientos Contables o Facturas (Cliente, Proveedor, rectificativas, etc, etc) y seleccionar, hacer clic en imprimir y luego Reporte Partida
	10) Reporte de Solicitud de Pagos: Ingresar a Contabilidad > Proveedores > Pagos Electronicos; Seleccionar rango de fechas, proveedor, concepto pago, nota de debito, fecha pago, facturas (agregar o quitar si hace falta alguna) y por ultimo, generar (PDF)

Funcionalidades:
	1) Calculo Automatico de Retención/Excencion de IVA y Retención de ISR: Se hace el calculo segun el regimen del contacto y de la empresa, para luego establecerlo en las cuentas de la configuracion del punto 1.1
	2) Al cargar la conciliacion, debera de incluir la referencia (ref), y debera hacer match con la referencia del archivo, para que coloque el contacto automaticamente