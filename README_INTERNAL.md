# Odoo Doc Studio - Documentación Técnica 🛠️

Este documento detalla la arquitectura y el funcionamiento interno del módulo para desarrolladores y administradores de sistemas.

## 🔒 Configuración Segura del Repositorio

Para un uso profesional, la documentación debe vivir fuera del código del módulo. Esto permite actualizaciones del módulo sin riesgo de pérdida de datos.

### Configuración Recomendada (Docker)

1.  **Mapeo de Volúmenes:**
    Monta una carpeta del host dentro del contenedor en tu `docker-compose.yml`:
    ```yaml
    volumes:
      - ./mi_repo_docu:/mnt/doc_studio_repo
    ```

2.  **Configurar Odoo:**
    No hardcodees rutas en el código. Usa los **Parámetros del Sistema**:
    *   **Clave:** `odoo_doc_studio.git_repo_path`
    *   **Valor:** `/mnt/doc_studio_repo` (La ruta dentro del contenedor).

---

## ⚙️ Arquitectura de Sincronización

El módulo implementa una estrategia de **Doble Pase + Poda** para garantizar que la Base de Datos y el Sistema de Archivos sean un espejo exacto.

### El Algoritmo (`sync_all_from_disk`)

1.  **Pase 1: Ingesta (Crear/Actualizar)**
    *   Escanea recursivamente el directorio configurado.
    *   Busca coincidencias por `file_path`.
    *   **Crea** registros para archivos nuevos.
    *   **Actualiza** el contenido si el archivo en disco ha cambiado.

2.  **Pase 2: Resolución de Jerarquía**
    *   Calcula los `parent_id` basándose en la estructura de carpetas (ej. `ventas/proceso.md` tiene como padre a `ventas.md`).

3.  **Pase 3: Poda (Eliminación de Huérfanos)**
    *   Elimina de Odoo cualquier registro cuyo archivo correspondiente haya desaparecido del disco.

### Gestión de Permisos de Archivo

Para permitir la edición fluida entre el Host (VS Code) y el Contenedor (Odoo), el módulo gestiona los permisos automáticamente:
*   **Directorios:** `chmod 777` (Permite al usuario del host borrar archivos creados por Docker).
*   **Archivos:** `chmod 666` (Permite la edición bidireccional sin bloqueos de "permission denied").

---

## 🚀 Migración desde Confluence

Para migrar una base de conocimientos desde Confluence a Doc Studio conservando la metadata, sigue esta estrategia:

### 1. Exportación de Datos
*   Usa herramientas como `confluence-to-markdown` o el exportador oficial de Confluence a HTML/Markdown.
*   Asegúrate de exportar los archivos adjuntos (imágenes, PDFs) a una carpeta local.

### 2. Mapeo de Metadata (Frontmatter)
Doc Studio detecta automáticamente la metadata si se incluye en el encabezado del archivo `.md`. Estructura tus archivos de la siguiente manera:

```markdown
---
title: Mi Página de Confluence
author: Juan Perez
created_at: 2023-01-01 10:00:00
last_editor: Maria Garcia
last_edited_at: 2024-01-01 12:00:00
---

# Contenido de la página...
```

### 3. Importación por Lotes
1. Detén el servidor Odoo o asegúrate de que el módulo no esté sincronizando.
2. Copia toda la estructura de carpetas exportada de Confluence al directorio configurado en `git_repo_path`.
3. Inicia Odoo y pulsa **"Sync All"** desde los Parámetros del Sistema o simplemente recarga la aplicación.
4. El sistema detectará los archivos, creará los registros y **reconstruirá la jerarquía** de Confluence basándose en las carpetas.

### 4. Resolución de Enlaces
Si los enlaces internos de Confluence se rompieron, puedes usar un script simple en Python para convertirlos al formato relativo `[Texto](../carpeta/pagina.md)` que Doc Studio entiende nativamente.

---

## 🎨 Editor Híbrido y Conversión

La potencia de Doc Studio reside en su capacidad de transformar formatos en tiempo real:

1.  **Conversión MD -> HTML:**
    *   Usa la librería `markdown` de Python.
    *   Resuelve enlaces dinámicos: `[texto](doc://id)` se convierte en una URL de acción de Odoo.
    *   Resuelve rutas relativas: `[texto](../guia.md)` busca el registro correspondiente en la DB y genera el enlace correcto.

2.  **Conversión HTML -> MD:**
    *   Usa `markdownify` para generar Markdown limpio desde el editor Wysiwyg.
    *   Transforma los enlaces de Odoo de vuelta al esquema `doc://` para que el archivo `.md` sea portable.

3.  **Lógica de Títulos Únicos:**
    *   El método `_ensure_unique_name` evita colisiones de archivos. Si intentas llamar a dos páginas "Test", la segunda se renombrará automáticamente a "Test (1)".

---

## 🔗 Acciones Especiales (RPC)

El frontend utiliza varios métodos del servidor para mantener la UX sincronizada:
*   `action_sync_to_disk`: Fuerza el guardado inmediato del contenido actual a un archivo físico.
*   `action_convert_md_to_html` / `action_convert_html_to_md`: Permiten la previsualización y el cambio de pestañas en tiempo real durante la edición.
