# Avatar — estudio de modelado v1

Primera interpretación 3D del retrato proporcionado. Modelado en Blender 5.2.1 LTS mediante geometría, materiales e iluminación; la imagen no se proyecta sobre el modelo.

## Archivos

- `avatar-model-v1.blend`: fuente editable con colecciones de rostro, cabello, sudadera, manos, pantalón/zapatillas y estudio. Incluye la referencia original empaquetada y una cámara de retrato.
- `avatar-model-v1.glb`: copia estática optimizada con materiales PBR. No contiene cámara, luces, suelo, rig ni animaciones.
- `portrait.png`, `front.png`, `side.png`: renders del modelo fuente.
- `glb-preview.png`: render del GLB después de volver a importarlo; muestra también las diferencias del material simplificado respecto a Blender.
- `model-report.json`: tamaño, geometría y comprobación de importación.

El rostro, los rizos, la sudadera grafito, los cordones y el bolsillo se basan en el retrato. La espalda, las manos y el cuerpo inferior son interpretaciones porque no aparecen completos en la referencia. Las manos están fuera de los bolsillos para poder revisar sus cinco dedos antes del rig.

## Estado y siguiente etapa

Es un modelo de revisión visual, no un `avatar-rigged.glb` listo para la web. El cuerpo todavía contiene superficies separadas en algunas uniones de ropa. Antes de animar hay que preparar la topología de hombros/codos, crear el esqueleto, asignar pesos y comprobar la deformación. La piel y la tela tienen detalles de shader en Blender que se simplifican al exportar materiales PBR.

La web y el avatar actual no se han modificado en esta etapa. Tras revisar el parecido se prepararán `Idle`, `Wave` y la integración.

## Reproducir

Desde la raíz del proyecto, en PowerShell:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python scripts/create-avatar-model.py
```

El comando regenera los archivos de esta carpeta. Guardar cualquier edición manual con otro nombre antes de ejecutarlo. Para volver a exportar el `.blend` existente sin regenerarlo:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python scripts/export-avatar-model.py
```
