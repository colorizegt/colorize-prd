# Aged Receivable - Número DTE (Odoo 17)

Módulo para Odoo 17 Enterprise que agrega el campo `account.move.fel_gt_dte_number`
al reporte **Cuentas por cobrar vencidas / Aged Receivable**.

## Comportamiento

- Agrega la columna **Número DTE**.
- La línea agrupada por cliente queda vacía porque un cliente puede tener varias facturas.
- Al desplegar el cliente, cada línea de detalle muestra el Número DTE correspondiente
  al `account.move` asociado al `account.move.line`.
- No modifica archivos estándar de Odoo Enterprise.
- La columna forma parte del motor `account.report`, por lo que también queda disponible
  para las exportaciones estándar del reporte.

## Instalación en Odoo.sh

1. Copiar la carpeta `aged_receivable_dte` al repositorio Git.
2. Hacer commit y push a la rama de staging.
3. Esperar que Odoo.sh termine el build.
4. En Apps, actualizar la lista de aplicaciones si es necesario.
5. Buscar **Aged Receivable - Número DTE** e instalarlo.
6. Abrir Contabilidad -> Informes -> Cuentas por cobrar vencidas.
7. Desplegar un cliente con facturas FEL y verificar la columna **Número DTE**.

## Actualización por terminal

Si el módulo ya está instalado y solo se actualizó el código:

```bash
odoo-bin -d <nombre_bd> -u aged_receivable_dte --stop-after-init
```

En Odoo.sh normalmente es preferible actualizar desde Apps si no se conoce con certeza
el nombre de la base de datos del build.
