# Entrega y validación del avatar

La infraestructura 3D está preparada. La versión 2.5D permanece activa hasta recibir y revisar el modelo.

Existe una primera versión de modelado en `models/avatar-v1/`: fuente Blender editable, GLB estático optimizado y renders frontal, lateral y de retrato. Es una propuesta visual basada en la ilustración, todavía sin esqueleto ni clips. No debe copiarse como `avatar-rigged.glb` hasta completar la preparación para animación.

La revisión de parecido más reciente está en `models/avatar-v2/`, con proporciones y rasgos ajustados, rizos irregulares, capucha en V y manos dentro del bolsillo. También sigue siendo un modelo estático; la v1 se conserva para comparar.

## Contrato para el modelador

Entregar `public/models/avatar-rigged.glb`, humanoide completo con el rostro, cabello rizado, sudadera oscura y acabado de la ilustración de referencia. Usar materiales PBR, texturas embebidas, eje Y vertical y frente hacia +Z. Aplicar escala uniforme; centrar el personaje. Objetivo: máximo 4 MiB, texturas de hasta 2048 px y preferiblemente menos de 50 000 triángulos.

Incluir una malla deformada por esqueleto y animaciones llamadas exactamente `Idle` y `Wave`, ambas de duración positiva. Idle debe cerrar en bucle; Wave debe levantar y agitar una mano y volver al reposo. Ambas animaciones deben permanecer en el sitio, sin desplazamiento de la raíz. Revisar pesos de hombro, codo, muñeca y dedos. No se requiere animación facial.

Exportar también un retrato transparente de la pose Idle para sustituir `src/assets/avatar/avatar-body.png` como imagen fallback: el archivo actual es un respaldo provisional procedente de las capas anteriores. Conservar los assets anteriores hasta aprobar el nuevo render. Evitar compresión Draco para que no se necesiten decodificadores externos en esta primera entrega.

## Activación local

1. Añadir el GLB y ejecutar `npm run avatar:check`.
2. Crear `.env.local` con `PUBLIC_AVATAR_3D_ENABLED=true`.
3. Iniciar/reiniciar el servidor con `npm run dev -- --background`; administrar con `npm run astro -- dev status`, `stop` y `logs`.
4. Revisar visualmente y ejecutar `npm run build`. La bandera se evalúa durante el build; cambiar el archivo en producción requiere reconstruir.

Si falta el archivo o la bandera está desactivada se conserva el componente anterior. Con 3D activado, un error de descarga, clips inválidos, ausencia de WebGL o pérdida del contexto muestra el retrato estático. No se ofrecen controles de saludo cuando no hay una escena interactiva disponible.

## Comportamiento y encuadre

La isla React carga la escena de forma diferida. Normaliza la altura del modelo y muestrea ambos clips para reservar espacio a la mano; la cámara se adapta al tamaño del contenedor. El hero coloca el texto y el avatar en columnas por encima de 1100 px y apila el avatar debajo del texto en tablet y móvil para evitar superposiciones. El paneo GSAP mueve el grupo dentro de ese espacio de +0.12 a -0.08 unidades normalizadas, en lugar del desplazamiento anterior en vw que sacaba al personaje del encuadre.

Wave se mezcla con Idle, se reproduce una vez al entrar y se repite con hover de ratón o activación mediante toque, Enter o Espacio. Las solicitudes durante el saludo y los 800 ms siguientes se descartan. El puntero gira el grupo un máximo de 3°; en pantallas táctiles no se aplica parallax. El movimiento reducido congela el primer fotograma Idle, sin saludo ni paneo. Fuera de pantalla se pausa la animación y el render continuo. DPR limitado a 1.5.

## Pruebas pendientes con el modelo real

- Revisar frente/perfil y saludo completo: sin huecos, extremidades duplicadas ni deformaciones de hombro/mano.
- Comparar contra la imagen original: rostro, pelo, sudadera y proporciones.
- Probar 320, 390, 768, 1024, 1440 y 1920 px, incluyendo alturas reducidas y cambio de orientación.
- Probar scroll en ambos sentidos, hover repetido, toque, Enter/Espacio y foco visible.
- Cambiar movimiento reducido con la página abierta; verificar pose estática y reanudación.
- Bloquear la petición GLB, usar un GLB sin clips, desactivar WebGL y simular pérdida de contexto: debe quedar visible el fallback.
- Medir carga transferida, frames por segundo y memoria en un móvil real; no se pueden certificar sin el asset.

Después de aprobar estas pruebas, se puede retirar `AvatarHeroLegacy.astro` y las capas de brazo/mano. Hasta entonces se conservan para revertir desactivando la bandera.
