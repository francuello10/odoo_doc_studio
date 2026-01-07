# Odoo Doc Studio 📚

**El Centro de Documentación Definitivo para Odoo.**

Doc Studio transforma Odoo en una plataforma de documentación potente y moderna que encanta tanto a desarrolladores como a usuarios de negocio. Combina la sencillez de una Wiki con la potencia de los flujos de trabajo basados en **Git y Markdown**.

## 🚀 ¿Por qué Doc Studio?

*   **Editor Híbrido Real:**
    *   **Usuarios de Negocio:** Editan cómodamente en Odoo con un editor visual (Wysiwyg).
    *   **Documentalistas/Desarrolladores:** Editan directamente la fuente en **Markdown** sin salir de la app.
    *   **Avanzados:** Acceso total al código fuente **HTML** para ajustes finos.
*   **Markdown Nativo:** Todo el contenido se guarda como archivos `.md` estándar. Sin bases de datos propietarias, 100% compatible con Obsidian, VS Code o GitHub.
*   **Sincronización Mágica:** Los cambios en el disco actualizan Odoo. Los cambios en Odoo actualizan el disco. Todo siempre en espejo.
*   **Flujo de Trabajo Fluido:** Al crear una página nueva, entras directamente en modo edición. Los títulos se mantienen únicos automáticamente (Smart Naming).

## ✨ Características Principales

1.  **Sincronización Bidireccional:**
    *   **Efecto Espejo:** Si borras un archivo en el disco, desaparece de Odoo al recargar.
    *   **Importación Automática:** Arrastra una carpeta de Markdown al repo y Odoo reconstruirá toda la jerarquía automáticamente.
2.  **Navegación Interna Inteligente:** Enlaza documentos usando rutas relativas estándar (ej. `[Guía](../folder/doc.md)`). Doc Studio los convierte en enlaces navegables dentro de Odoo.
3.  **Gestión Masiva:** Vista de lista dedicada para operaciones por lote (borrado, exportación, etiquetado).
4.  **Integración con Git:** Preparado para sincronizar con repositorios remotos (GitHub/GitLab) desde la propia configuración.

---

## 📊 Comparativa: Doc Studio vs Otros

| Característica | **Doc Studio** | Confluence | Google Docs | Docusaurus | Odoo Knowledge |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Formato de Guardado** | **Markdown (.md)** | Propietario | Propietario | Markdown | Propietario (HTML) |
| **Control de Versiones** | **Git Nativo** | Historial interno | Historial interno | Git | Historial interno |
| **Editor** | **Híbrido (Vis/MD/HTML)** | Visual | Visual | Solo Código | Visual |
| **Integración ERP** | **Total (Natívo Odoo)** | Ninguna | Ninguna | Ninguna | Total |
| **Offline-first** | **Sí (vía VS Code/Git)** | No | Limitado | Sí | No |
| **Portabilidad** | **Máxima (Filesystem)** | Baja | Baja | Alta | Baja |

*   **vs Confluence:** Doc Studio es más rápido, permite a los devs usar sus propias herramientas y los datos te pertenecen (están en archivos .md).
*   **vs Google Docs:** Google Docs es mejor para colaboración en tiempo real de marketing, pero Doc Studio es superior para documentación técnica y de procesos estructurados.
*   **vs Docusaurus:** Ideal para sitios estáticos externos; Doc Studio ofrece lo mismo pero integrado dentro de la plataforma donde vive tu empresa.
*   **vs Odoo Knowledge:** Knowledge es excelente pero sus datos están "atrapados" en la DB. Doc Studio permite que esa misma documentación sea accesible desde un terminal o un IDE.

---

## 🛠️ Configuración

Para vincular Doc Studio con tu repositorio o carpeta externa:

1.  Ve a **Ajustes -> Técnico -> Parámetros del Sistema**.
2.  Busca o crea la clave: `odoo_doc_studio.git_repo_path`.
3.  Valor: La ruta absoluta a tu carpeta de documentación (ej. `/home/user/my-docs`).

*¡Listo! No se requieren cambios de código.*

---

## 👩‍💻 Flujo de Trabajo para el Usuario

1.  **Crear:** Pulsa "New" y empieza a escribir inmediatamente.
2.  **Importar:** Si tienes un documento en Markdown de otro sitio, pulsa "Edit", ve a la pestaña "Markdown" y pégalo directamente.
3.  **Enlazar:** Usa `[Nombre](doc://id)` o simplemente el nombre del archivo para navegar entre páginas.
4.  **Sincronizar:** Si editas desde VS Code, simplemente pulsa "Sync" en Odoo y verás tus cambios reflejados.
