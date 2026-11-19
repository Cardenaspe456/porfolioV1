# Portafolio DEV.

Prototipo editorial construido con Astro. Fondo claro, azul técnico, tipografía de sistema y paneles con bordes finos. Todo el contenido profesional es provisional.

## Organización

- `src/pages/`: rutas. La portada compone secciones; `proyectos/[slug].astro` genera los tres casos de estudio.
- `src/layouts/`: documento HTML y estructura compartida.
- `src/components/layout/`: cabecera y pie.
- `src/components/sections/`: presentación, proyectos, sobre mí, experiencia, habilidades y contacto.
- `src/components/ui/`: tarjetas y encabezados reutilizables.
- `src/data/projects.ts`: datos tipados compartidos por las tarjetas y los detalles.
- `src/styles/global.css`: variables visuales, estilos compartidos y adaptación responsive.
- `src/components/avatar/` y componentes AvatarHero: integración anterior conservada, sin cargar en el prototipo.

## Desarrollo

Requiere Node >=22.12.0 y dependencias instaladas con `npm install`.

```sh
node node_modules/astro/bin/astro.mjs dev --background
node node_modules/astro/bin/astro.mjs dev status
node node_modules/astro/bin/astro.mjs dev logs
node node_modules/astro/bin/astro.mjs dev stop
npm run build
npm run typecheck
```

## Personalización

Reemplazar primero los proyectos en `src/data/projects.ts`. Cambiar biografía, experiencia y habilidades en sus componentes de sección. Completar nombre en la cabecera y metadatos del layout. Añadir correo, perfiles y CV en Contact antes de publicar. No hay formulario ni enlaces externos ficticios.

Las áreas visuales de proyecto son espacios editoriales reservados para futuras capturas reales. No representan productos realizados. El avatar se conserva para una integración posterior; consultar `docs/avatar-3d.md`.
