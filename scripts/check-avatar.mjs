import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const path = resolve(process.argv[2] ?? 'public/models/avatar-rigged.glb');
try {
  const bytes = await readFile(path);
  if (bytes.length < 20 || bytes.readUInt32LE(0) !== 0x46546c67 || bytes.readUInt32LE(4) !== 2
    || bytes.readUInt32LE(8) !== bytes.length) throw new Error('Cabecera GLB 2.0 inválida.');
  const jsonLength = bytes.readUInt32LE(12);
  if (bytes.readUInt32LE(16) !== 0x4e4f534a || 20 + jsonLength > bytes.length) throw new Error('Chunk JSON inválido.');
  const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString('utf8').trim());
  const errors = [];
  if (bytes.length > 4 * 1024 * 1024) errors.push('El modelo supera 4 MiB.');
  if (!gltf.skins?.some(skin => skin.joints?.length)) errors.push('Falta un esqueleto con articulaciones.');
  if (!gltf.nodes?.some(node => node.mesh !== undefined && node.skin !== undefined)) errors.push('Falta una malla vinculada al esqueleto.');
  for (const name of ['Idle', 'Wave']) {
    const clip = gltf.animations?.find(animation => animation.name === name);
    if (!clip?.channels?.length || !clip.samplers?.length) errors.push(`Falta el clip ${name} o está vacío.`);
  }
  if ([...(gltf.buffers ?? []), ...(gltf.images ?? [])].some(asset => asset.uri && !asset.uri.startsWith('data:'))) errors.push('Hay recursos externos: deben ir embebidos.');
  if (gltf.extensionsRequired?.includes('KHR_draco_mesh_compression')) errors.push('Exportar sin Draco para evitar decodificadores externos.');
  if (errors.length) throw new Error(errors.join('\n'));
  console.log(`Contrato estructural válido: ${(bytes.length / 1048576).toFixed(2)} MiB; Idle, Wave y esqueleto presentes. Falta aprobación visual.`);
} catch (error) {
  console.error(error.code === 'ENOENT' ? `PENDIENTE: entregar ${path}` : error.message);
  process.exitCode = 1;
}
