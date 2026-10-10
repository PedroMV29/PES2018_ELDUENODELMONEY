# PES 2018 DueñodelMundo — v3.4

Editor **no oficial** de presupuestos de fichajes y salarios base de Liga Máster para PES 2018 en Windows. No afiliado a KONAMI.

## Funciones
- Detecta y selecciona partidas `ML00000000`, `ML00000001` y otras `ML` compatibles.
- Lee los presupuestos base de una partida.
- Genera un archivo modificado independiente.
- Permite aplicar cambios directamente a la partida, con confirmación y copia de seguridad.
- Interfaz compacta; restauración de valores leídos en los campos.

## Requisitos para usarlo
- Windows 10/11.
- **pesXdecrypter 4.0.0**, descargado por separado de una fuente que el usuario considere confiable. La carpeta seleccionada debe contener `decrypter18.exe` y `encrypter18.exe`.
- Si usas el `.exe` distribuido en Releases, **no necesitas instalar Python**.

**Nota:** `pesXdecrypter` no se incluye ni se redistribuye en este repositorio. Verifica su procedencia y los permisos de uso antes de descargarlo. No hay un enlace oficial verificado incluido aquí.

## Uso
1. Haz una copia de seguridad de tus archivos de Liga Máster.
2. Descarga el ejecutable desde la sección *Releases* (cuando esté publicado) o compílalo como se indica abajo.
3. Abre la aplicación y entra en **Configuración de carpetas** para seleccionar la carpeta que contiene `decrypter18.exe` y `encrypter18.exe`.
4. Selecciona una partida y pulsa **LEER PRESUPUESTOS**.
5. Introduce nuevos importes en dólares (múltiplos de 100) y elige **GENERAR ARCHIVO MODIFICADO** o **APLICAR DIRECTAMENTE A LA PARTIDA**.
6. **Cierra PES 2018 antes de aplicar directamente.** Confirma la operación solo si reconoces la partida y los importes.

Los salarios *base* almacenados pueden diferir del saldo salarial visible en el juego. La calibración de saldo visible para `ML00000001` proviene de una prueba concreta y **no es universal**.

## Compilar el ejecutable en Windows
Requiere Python 3 y conexión para instalar PyInstaller. Ejecuta `CREAR_EXE.bat`; el resultado aparecerá en `dist/PES2018_ELDUEÑODELMONEY.exe`.

## Crear el instalador
Requiere Inno Setup 6. Tras compilar el `.exe`, abre `INSTALADOR.iss` en Inno Setup y selecciona **Compile**. El instalador se generará en `instalador/`.

## Seguridad y privacidad
- No subas a GitHub tus partidas `ML*`, respaldos, configuraciones personales ni datos de la carpeta `save`.
- No modifiques partidas sin conservar un respaldo adicional fuera de la carpeta del juego.
- La edición de archivos guardados tiene riesgos y puede no funcionar con todas las partidas o temporadas.
- El programa se proporciona sin garantía de compatibilidad universal.

## Licencia y atribuciones
**Pendiente de definir antes de publicar.** Elige una licencia apropiada únicamente para el código que tengas derecho a distribuir. No incluye derechos sobre PES 2018 ni sobre `pesXdecrypter`.
