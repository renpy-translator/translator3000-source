# Translator3000 — Código fuente reconstruido

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <strong>Español</strong>
</p>

> Una reconstrucción legible y lista para seguir desarrollándose de **Translator3000** (versión original `1.45.11`) para juegos Ren'Py: recuperada del `Translator3000.rpa` distribuido, totalmente desofuscada, y capaz de empaquetarse de nuevo en un único `Translator3000.rpa` listo para colocar en un juego.

Translator3000 traduce automáticamente juegos Ren'Py mientras juegas: captura los diálogos y menús, los envía a un servicio de traducción, guarda cada resultado en una base de datos propia de cada juego y muestra la traducción en lugar del texto original. Este repositorio existe porque el código fuente actual (v3) de Translator3000 no está disponible públicamente, y el antiguo código público v2 lleva años desactualizado. Aquí, la compilación original más reciente ha sido reconstruida a código fuente limpio para que la comunidad pueda estudiarla, corregirla y desarrollar nuevas funciones sobre ella.

---

## ✨ Características

### Traducción

- **Traducción en tiempo real** de diálogos y menús de opciones mientras juegas.
- **Cuatro modos de trabajo**: Desactivado, Preescaneo (traducir todo el juego por adelantado), Solo BD (mostrar solo traducciones ya presentes en la base de datos) y Tiempo real + BD.
- **Muchos servicios integrados**: Google (GTX / client5 / RPC), Bing, DeepL (API oficial, RPC, Selenium), Yandex, Reverso y LingvaNex.
- **Base de datos de traducción por juego**: cada línea traducida se guarda en caché, así que rejugar una escena no consume nuevas peticiones; si hay una base de datos lista en la nube, se reutiliza.
- División en frases al traducir, control de frecuencia de peticiones, compatibilidad con proxy y Tor, y sustitución de variables desde la base de datos.

### Panel dentro del juego

- Panel de ajustes que se abre dentro de cualquier juego, con controles de servicio de traducción, dirección de idiomas y modo de trabajo.
- Ajustes de fuente y del texto mostrado (tamaño, color, contornos, capas), selección automática de fuente según el idioma de destino.
- Editor de variables del juego, editor de texto, combinaciones de teclas personalizadas, temas de color y una ventana del traductor que se puede arrastrar y redimensionar.
- Canal de notificaciones, estadísticas, gestión de la caché de traducción y copia de seguridad de la base de datos.

### Idiomas de la interfaz

- Interfaz disponible en **inglés (predeterminado)**, ruso, vietnamita, chuvasio y turco.
- El vietnamita es una novedad de esta reconstrucción, con cobertura completa de cadenas.

### Compatibilidad

- Compatible con juegos hechos con **Ren'Py 7 (Python 2)** y **Ren'Py 8 (Python 3)** desde el mismo archivo: los árboles de módulos `py2` / `py3` se empaquetan al compilar.
- Se distribuye como **un único archivo `.rpa`**: cópialo en la carpeta `game` de un juego y funciona, sin necesidad de otros archivos.

---

## 🚀 Instalación

1. Compila el paquete (ver [Compilación](#-compilación)) o usa un `build/Translator3000.rpa` ya compilado.
2. Copia `Translator3000.rpa` en la carpeta `game` de tu juego Ren'Py.
3. Inicia el juego y abre el panel de Translator3000 con su tecla de acceso rápido para configurar un servicio de traducción y un modo de trabajo.

> No copies archivos `.py` / `.rpy` sueltos en el juego: los archivos sueltos tienen prioridad sobre los que están dentro del RPA. Ren'Py carga automáticamente cada `.rpa` de la carpeta `game`.

---

## 📖 Uso

1. Abre el panel de Translator3000 en el juego.
2. Elige un **servicio de traducción** y define los **idiomas de origen / destino**.
3. Elige un modo de trabajo:
   - **Preescaneo**: traduce el juego completo a la base de datos por adelantado (la mejor experiencia después).
   - **Solo BD**: muestra las traducciones que ya están en la base de datos.
   - **Tiempo real + BD**: usa primero la base de datos y traduce en vivo las líneas que falten.
   - **Desactivado**: texto original.
4. Para cambiar el idioma de la interfaz, usa el botón de idioma del panel (`EN` / `VI` / `RU` / …). El inglés es el predeterminado en el primer inicio.

---

## 🔧 Compilación

Requisitos:

- Python 3 (ejecuta `build.py` y empaqueta el árbol de módulos `py3`).
- Un intérprete de Python 2.7 (empaqueta el árbol de módulos `py2` en `.tr3000py`).
- Un ejecutable de un juego o SDK de Ren'Py 7 (compila los `.rpy` a `.rpyc`).

```text
python build.py --renpy7-exe "C:\path\to\RenPy7Game.exe" --python2 "C:\path\to\python27\python.exe"
```

Salida: `build/Translator3000.rpa` (RPA-3.0).

Cómo funciona: los archivos `.rpy` se compilan con Ren'Py 7 en una carpeta temporal, los módulos `.py` se codifican en el formato original `.tr3000py` (AST → pickle → base64 → zlib, el formato que espera el `PyLoader` original), y todo se empaqueta en un solo RPA con exactamente la misma estructura en tiempo de ejecución que la versión original.

### Estructura del repositorio

```text
src/
  000translator3000_main.rpy        script principal (GUI + núcleo, desofuscado)
  translations/                     cadenas de la interfaz (EN / VI / RU / CV / TR)
  _translator3000_main_modules/
    py2/_translator3000/*.py        módulos para juegos Ren'Py 7
    py3/_translator3000/*.py        módulos para juegos Ren'Py 8
  _translator3000_extra_modules/    bibliotecas incluidas
  old_requests_module/  old_pkgutil_module/  uuid_py3_fix/  _extra_six.py
  Translator3000OtherFiles/         fuentes, imágenes de la GUI, patrones
tools/                              herramientas de desofuscación y generadores de traducción
build.py                            constructor del paquete
```

### Cómo se reconstruyó el código fuente

El archivo original se desempaquetó, su `.rpyc` se descompiló con unrpyc (parcheado para leer el código Python almacenado por el autor como AST), y sus módulos `.tr3000py` se decodificaron desde pickles AST comprimidos de vuelta a código Python. Después, un paso seguro de plegado estático convirtió las cadenas divididas / ofuscadas aritméticamente por el autor en literales normales (por ejemplo, `__version__ = '1.45.11'`). Los comentarios y el formato original son irrecuperables por naturaleza; la ofuscación dinámica y los identificadores renombrados por Ren'Py se mantienen tal cual para preservar el comportamiento.

---

## 🗺️ Hoja de ruta

Completado en esta reconstrucción:

- [x] Desempaquetado completo del `Translator3000.rpa` original (660 archivos)
- [x] Descompilación del script principal y de todos los módulos `py2` / `py3`
- [x] Desofuscación estática a código fuente legible
- [x] Idioma de interfaz en vietnamita, inglés como idioma de interfaz predeterminado
- [x] Correcciones de compatibilidad con Ren'Py 8 (forma de `exec` válida en Python 2/3, literales enteros largos)
- [x] Compilación con un solo comando de vuelta a un `Translator3000.rpa` listo para usar
- [x] Carga e inicialización verificadas en Ren'Py 7.3.5 y Ren'Py 8.5.3
- [x] Proveedor de traducción OpenAI / ChatGPT (clave API, base URL y modelo personalizables, traducción por lotes con contexto)
- [x] Traducción de la interfaz del juego (menús, preferencias, pantallas de guardar/cargar) con el mismo proveedor y la misma base de datos
- [x] Exportación / importación de bases de datos de traducción (copias de seguridad, compartir entre equipos)
- [x] Cambio rápido de modo (insignia en pantalla y tecla de acceso rápido para alternar Desactivado ↔ Solo BD en mitad del juego)
- [x] Opción para desactivar la comprobación forzada de actualizaciones

Funciones planeadas (las contribuciones son bienvenidas):

- [ ] Ajuste automático del texto traducido a su marco y selección automática de fuente más inteligente (vietnamita, CJK…)
- [ ] Glosario por juego / términos que no deben traducirse y marcadores protegidos
- [ ] Más idiomas de interfaz (简体中文, 日本語, Español…)
- [ ] Matriz de pruebas automática de Ren'Py 7 / Ren'Py 8 y compilaciones del RPA con CI en las etiquetas de versión
- [ ] Archivos de versión precompilados adjuntos a GitHub Releases

---

## 🤝 Contribuir

Son bienvenidos los issues y los pull requests.

- Para un error, incluye la versión de Ren'Py, el nombre del juego, tu modo de trabajo y servicio de traducción, y las líneas relevantes del registro / traceback.
- Edita la lógica de Ren'Py en `src/000translator3000_main.rpy`, los módulos de traducción en el árbol `py2` / `py3` correspondiente y las cadenas de la interfaz en `src/translations/`, y luego recompila con `build.py`.
- Cuando toques código compartido, prueba al menos en un juego Ren'Py 7 y en un juego Ren'Py 8.

## 🙏 Créditos

Translator3000 fue creado por **Vladya**; este repositorio es una reconstrucción comunitaria de su compilación original más reciente, con fines de mantenimiento y de desarrollo futuro. El antiguo código público v2 solo sirvió como referencia estructural: no se usa código v2.

## 📄 Licencia

Translator3000 y Ren'Py son obra de sus respectivos autores. Revisa los términos de los proyectos originales antes de redistribuir; este repositorio documenta un esfuerzo de reconstrucción y añade sobre él herramientas de mantenimiento y traducciones.
