import platformDrawing from '../assets/blueprints/plataforma.webp';
import editorialDrawing from '../assets/blueprints/editorial.webp';
import componentDrawing from '../assets/blueprints/componentes.webp';

export interface Project {
  slug: string;
  number: string;
  title: string;
  category: string;
  drawing: ImageMetadata;
  drawingAlt: string;
  drawingCaption: string;
  summary: string;
  technologies: string[];
  role: string;
  problem: string;
  solution: string;
  decisions: string[];
  result: string;
}

export const projects: Project[] = [
  {
    slug: 'plataforma-de-producto', number: '01', title: 'Plataforma de producto', category: 'Aplicación web / Frontend',
    drawing: platformDrawing,
    drawingAlt: 'Plano axonométrico de un panel de control con navegación, gráficos y una vista lateral de detalle.',
    drawingCaption: 'Estructura del panel de control',
    summary: 'Una interfaz para organizar información y convertir tareas complejas en acciones sencillas.',
    technologies: ['React', 'TypeScript', 'CSS'], role: 'Diseño de interfaz y desarrollo frontend',
    problem: 'Ejemplo: un equipo necesita consultar y organizar información desde distintas pantallas sin perder el contexto de su trabajo.',
    solution: 'Propuesta: una plataforma con navegación consistente, vistas de resumen y componentes reutilizables para las tareas principales.',
    decisions: ['Agrupar la información por tarea y prioridad.', 'Reutilizar patrones de navegación y estados de interfaz.', 'Adaptar la densidad de información al tamaño de pantalla.'],
    result: 'Pendiente de documentar con un proyecto real: validación con usuarios, resultados y aprendizajes.',
  },
  {
    slug: 'experiencia-editorial', number: '02', title: 'Experiencia editorial', category: 'Sitio web / Diseño y desarrollo',
    drawing: editorialDrawing,
    drawingAlt: 'Dos páginas de una publicación web en despiece, con sus columnas de texto y retículas tipográficas.',
    drawingCaption: 'Retícula de una página de lectura',
    summary: 'Un espacio de lectura donde la tipografía, la estructura y el contenido llevan el ritmo.',
    technologies: ['Astro', 'TypeScript', 'Tailwind'], role: 'Estructura de contenido y desarrollo web',
    problem: 'Ejemplo: una publicación necesita presentar artículos de distintas categorías con una lectura cómoda y una navegación directa.',
    solution: 'Propuesta: un sitio estático con jerarquía tipográfica, páginas de artículo y una estructura de contenido reutilizable.',
    decisions: ['Priorizar la legibilidad y el ancho de lectura.', 'Separar contenido, rutas y componentes.', 'Reducir el JavaScript necesario para leer y navegar.'],
    result: 'Pendiente de documentar con un proyecto real: rendimiento medido y experiencia de lectura validada.',
  },
  {
    slug: 'sistema-de-interfaces', number: '03', title: 'Sistema de interfaces', category: 'Sistema de diseño / UI',
    drawing: componentDrawing,
    drawingAlt: 'Despiece de una biblioteca de interfaz con campos, botones y controles de selección.',
    drawingCaption: 'Anatomía de los componentes',
    summary: 'Un lenguaje compartido de componentes para construir productos con mayor consistencia.',
    technologies: ['Figma', 'CSS', 'TypeScript'], role: 'Diseño de componentes y documentación',
    problem: 'Ejemplo: varias pantallas resuelven las mismas necesidades con estilos y comportamientos diferentes.',
    solution: 'Propuesta: una biblioteca de componentes con reglas visuales comunes, estados accesibles y ejemplos de uso.',
    decisions: ['Definir variables de color, tipografía y espaciado.', 'Documentar estados y comportamiento por componente.', 'Comprobar navegación por teclado y contraste.'],
    result: 'Pendiente de documentar con un proyecto real: adopción del sistema, mejoras y limitaciones.',
  },
];
