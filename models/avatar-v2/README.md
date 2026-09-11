# Avatar — revisión de parecido v2

Revisión de la primera versión para acercarse al retrato original. Los archivos de `models/avatar-v1/` se conservan.

Cambios principales:

- Cabeza más estrecha y de menor tamaño respecto al torso, con mandíbula redondeada.
- Ojos ligeramente más pequeños; cejas más cortas y finas, sonrisa más contenida y nariz ajustada.
- Orejas simplificadas, piel más cálida y acabados menos brillantes.
- Rizos redondeados con distribución irregular, sin las filas horizontales del primer modelo.
- Capucha de tela doblada con apertura en V, sustituyendo el cuello acolchado circular.
- Bolsillo canguro más ancho y mangas dobladas hacia él; manos completas conservadas dentro del bolsillo.
- Cámara de tres cuartos más próxima a la orientación de la referencia.

## Archivos

- `avatar-model-v2.blend`: fuente editable, con referencia empaquetada y estudio de iluminación.
- `avatar-model-v2.glb`: exportación estática optimizada, sin esqueleto ni clips.
- `portrait.png`: retrato renderizado del modelo fuente.
- `reference-view.png`: vista de 1672 × 941, las mismas dimensiones que la imagen original, sobre fondo oscuro.
- `front.png` y `side.png`: vistas de revisión del cuerpo completo.
- `glb-preview.png`: render de la exportación después de importarla de nuevo en Blender.
- `model-report.json`: número de triángulos, tamaño y comprobación de importación.

Es una interpretación modelada a partir de una sola vista. La espalda y las partes ocultas requieren interpretación. El acabado de tela de Blender se simplifica en los materiales PBR del GLB. No se presenta como una reproducción exacta.

Las manos están modeladas, pero la pose todavía es estática. Antes del saludo faltan preparar las uniones para deformación, el esqueleto, los pesos y los clips `Idle` y `Wave`. La web sigue utilizando el avatar anterior.

## Regenerar

Desde la raíz del repositorio:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python scripts/create-avatar-model-v2.py
```

El comando regenera esta carpeta. Guardar cualquier edición manual del `.blend` con otro nombre antes de ejecutarlo. Para exportar el archivo existente sin reconstruirlo:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python scripts/export-avatar-model-v2.py
```
