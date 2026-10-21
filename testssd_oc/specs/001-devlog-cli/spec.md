# Feature Specification: DevLog CLI

**Feature Branch**: `001-devlog-cli`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Quiero construir DevLog CLI, una herramienta de consola para guardar notas de desarrollo en SQLite. Permite crear, listar, buscar por etiquetas y exportar notas a Markdown. No necesita autenticación ni interfaz gráfica compleja"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guardar una nota de desarrollo (Priority: P1)

Como desarrollador que acaba de resolver un problema o ha guardado un comando útil, quiero
registrar esa nota desde la terminal con un título, un texto opcional y etiquetas, y tener la
certeza de que queda guardada de forma permanente, para no perder ese conocimiento.

**Why this priority**: sin captura de notas no existe el producto; todas las demás capacidades
(listar, buscar, exportar) dependen de que haya notas guardadas.

**Independent Test**: se puede probar de forma independiente ejecutando la creación de una nota
con título, contenido y etiquetas, y verificando después que la nota aparece en el listado
general; aporta valor por sí sola como cuaderno de notas.

**Acceptance Scenarios**:

1. **Given** una instalación nueva sin base de datos, **When** el usuario crea una nota con
   título "Error de CORS en staging", contenido descriptivo y las etiquetas `bug` y `api`,
   **Then** la nota queda guardada y se muestra un mensaje de confirmación con su fecha de
   creación.
2. **Given** el usuario en la terminal, **When** crea una nota indicando únicamente un título,
   **Then** la nota se guarda correctamente y el contenido y las etiquetas quedan vacíos.
3. **Given** una nota guardada, **When** el usuario cierra la terminal y vuelve a abrirla más
   tarde, **Then** la nota sigue disponible y aparece en el listado.

---

### User Story 2 - Consultar mis notas (Priority: P2)

Como desarrollador con cientos de notas acumuladas, quiero ver un listado de todas mis notas con
su título, fecha y etiquetas, para orientarme rápidamente sobre lo que tengo guardado sin abrir
archivos uno por uno.

**Why this priority**: una vez que las notas se acumulan, recuperarlas es el siguiente valor
principal; es la capacidad que hace útil el cuaderno a diario.

**Independent Test**: se puede probar de forma independiente creando varias notas con fechas
distintas y comprobando que el listado las devuelve todas, ordenadas de la más reciente a la más
antigua y con título, fecha y etiquetas visibles.

**Acceptance Scenarios**:

1. **Given** tres notas guardadas con fechas diferentes, **When** el usuario pide el listado,
   **Then** aparecen las tres con su título, fecha de creación y etiquetas, ordenadas de más
   reciente a más antigua.
2. **Given** un usuario que todavía no tiene ninguna nota, **When** pide el listado, **Then** la
   herramienta informa de que no hay notas guardadas y no muestra un error.
3. **Given** una nota guardada sin etiquetas, **When** el usuario pide el listado, **Then** esa
   nota aparece igualmente, mostrando que no tiene etiquetas.

---

### User Story 3 - Buscar notas por etiqueta (Priority: P3)

Como desarrollador que recuerda que resolvió un problema de autenticación pero no la fecha ni el
contenido exacto, quiero filtrar mis notas por una o más etiquetas, para recuperar en segundos
las notas relevantes.

**Why this priority**: la búsqueda convierte el cuaderno en una herramienta de consulta y es el
principal ahorro de tiempo frente a leer el listado completo.

**Independent Test**: se puede probar de forma independiente creando notas con combinaciones
distintas de etiquetas y verificando que la búsqueda devuelve exactamente las notas que
coinciden con la etiqueta solicitada y ninguna otra.

**Acceptance Scenarios**:

1. **Given** notas con las etiquetas `bug`, `api` y `idea`, **When** el usuario busca por `bug`,
   **Then** solo se devuelven las notas que tienen esa etiqueta.
2. **Given** una etiqueta que no existe en ninguna nota, **When** el usuario busca por ella,
   **Then** la herramienta informa de que no hay coincidencias y no devuelve resultados.
3. **Given** un resultado de búsqueda, **When** se muestra, **Then** cada nota devuelta incluye
   su título, fecha y etiquetas para poder identificarla.

---

### User Story 4 - Exportar mis notas a Markdown (Priority: P4)

Como desarrollador que quiere compartir su base de conocimiento con el equipo o archivarla, quiero
exportar todas mis notas a un archivo Markdown legible, para poder revisarlo, versionarlo o
publicarlo fuera de la herramienta.

**Why this priority**: la exportación es la vía para sacar el valor del cuaderno fuera de la
herramienta; es valuable pero no necesaria para el uso diario dentro de la terminal.

**Independent Test**: se puede probar de forma independiente exportando un conjunto conocido de
notas y verificando que el archivo Markdown generado contiene cada nota con su título, fecha,
etiquetas y contenido, sin perder información.

**Acceptance Scenarios**:

1. **Given** notas guardadas, **When** el usuario pide la exportación, **Then** se genera un
   archivo Markdown que contiene todas las notas con título, fecha de creación, etiquetas y
   contenido.
2. **Given** un archivo Markdown ya existente en la ruta de destino, **When** el usuario intenta
   exportar, **Then** la herramienta pide confirmación explícita antes de reemplazarlo.
3. **Given** notas con contenido que incluye saltos de línea, listas o caracteres especiales,
   **When** se exportan, **Then** el archivo Markdown conserva ese contenido de forma legible y
   no corrompido.

---

### Edge Cases

- ¿Qué ocurre en el primer uso, cuando todavía no existe el almacén de datos? La herramienta lo
  crea automáticamente sin pedir nada y sin tocar ningún dato previo.
- ¿Qué ocurre si el archivo de la base de datos existe pero está dañado o no se puede leer? La
  herramienta muestra un error claro, explica qué hacer y no borra, recrea ni reinicia el archivo
  de forma automática.
- ¿Qué ocurre si el usuario introduce un título vacío o formado solo por espacios? La
  herramienta rechaza la nota con un mensaje de validación comprensible y no guarda nada.
- ¿Qué ocurre si el usuario repite la misma etiqueta o la escribe con distinta capitalización? La
  etiqueta se normaliza (recortada y en minúsculas) y no se almacena duplicada dentro de la
  misma nota.
- ¿Qué ocurre si el usuario busca por una etiqueta que no existe? Se informa de que no hay
  coincidencias, con un código de salida que indica que no fue un error técnico.
- ¿Qué ocurre si la búsqueda no devuelve resultados y el usuario pide además el listado normal?
  Ambas operaciones son independientes y funcionan por separado.
- ¿Qué ocurre si el usuario exporta cuando no tiene ninguna nota? La herramienta genera un
  archivo Markdown vacío pero válido, e informa de que no había notas que exportar.
- ¿Qué ocurre si el usuario indica una ruta de exportación en un directorio inexistente o sin
  permisos de escritura? La herramienta muestra un error claro y no deja archivos parciales.
- ¿Qué ocurre si el contenido de una nota contiene comillas, saltos de línea o caracteres de
  Markdown? El contenido se conserva íntegro y se representa de forma segura en la exportación.
- ¿Qué ocurre si dos operaciones concurrentes intentan escribir a la vez? La herramienta
  completa una operación y la otra recibe un mensaje claro, sin corromper los datos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir al usuario crear una nota con un título obligatorio, un
  contenido opcional y cero o más etiquetas.
- **FR-002**: El sistema MUST asignar a cada nota un identificador único, su fecha y hora de
  creación, y MUST conservarlos durante toda la vida de la nota.
- **FR-003**: El sistema MUST persistir las notas en un almacén de datos local y MUST resolver
  la ubicación y el ciclo de vida de ese almacén — [NEEDS CLARIFICATION: ¿en qué ruta exacta debe
  vivir el archivo de base de datos (por ejemplo, una ruta fija bajo el directorio personal del
  usuario o un archivo en el directorio actual), y se confirma que la herramienta nunca borra ni
  reinicia un almacén existente sin una aprobación explícita del usuario en ese momento?]
- **FR-004**: El sistema MUST conservar los datos de las notas entre ejecuciones: cerrar la
  herramienta o reiniciar el equipo no debe alterar las notas guardadas.
- **FR-005**: El sistema MUST listar las notas guardadas por el usuario.
- **FR-006**: El listado MUST mostrar, como mínimo, el título, la fecha de creación y las
  etiquetas de cada nota.
- **FR-007**: El listado MUST ordenar las notas de la más reciente a la más antigua.
- **FR-008**: El listado MUST ejecutarse sin exigir ningún filtro y MUST indicar de forma
  explícita cuando no exista ninguna nota guardada.
- **FR-009**: El sistema MUST buscar notas a partir de una o más etiquetas indicadas por el
  usuario.
- **FR-010**: El alcance de la búsqueda MUST [NEEDS CLARIFICATION: ¿la coincidencia de etiqueta
  debe ser exacta o debe admitir coincidencias parciales por subcadena, y cuando se indican
  varias etiquetas el resultado debe exigir todas ellas (Y) o basta con que coincida alguna
  (O)?]
- **FR-011**: El resultado de una búsqueda MUST mostrar título, fecha y etiquetas de cada nota
  coincidente y MUST distinguir de forma clara el caso sin coincidencias.
- **FR-012**: El sistema MUST exportar las notas guardadas a un archivo Markdown — alcance de la
  gestión de notas existentes MUST [NEEDS CLARIFICATION: ¿el alcance se limita a las cuatro
  capacidades indicadas en la entrada (crear, listar, buscar por etiquetas y exportar), o se
  incluye además la edición y el borrado de notas ya creadas?]
- **FR-013**: La exportación MUST incluir, para cada nota, su título, su fecha de creación, sus
  etiquetas y su contenido, en un formato Markdown legible.
- **FR-014**: La exportación MUST ofrecer al usuario la posibilidad de elegir la ruta del archivo
  de destino y MUST informar del resultado de la operación.
- **FR-015**: El sistema MUST NOT sobrescribir un archivo de exportación existente sin una
  confirmación explícita del usuario en ese momento.
- **FR-016**: El sistema MUST validar que el título de una nota no sea vacío ni contenga
  únicamente espacios, y MUST informar del error sin guardar nada.
- **FR-017**: El sistema MUST normalizar las etiquetas (recortar espacios y unificar mayúsculas
  y minúsculas) y MUST NOT almacenar dos veces la misma etiqueta dentro de una misma nota.
- **FR-018**: El sistema MUST conservar íntegro el contenido de la nota, incluidos saltos de
  línea y caracteres especiales, y MUST representarlo de forma segura en la exportación.
- **FR-019**: El sistema MUST NOT ejecutar operaciones destructivas sobre el almacén de datos
  (borrado, reinicio o recreación del esquema) de forma automática ni implícita: cualquier
  operación de ese tipo requiere la aprobación explícita del usuario en ese momento.
- **FR-020**: El sistema MUST mostrar mensajes de error comprensibles, sin trazas técnicas, que
  indiquen qué ha fallado y qué acción ha de realizar el usuario.
- **FR-021**: El sistema MUST comunicar el resultado de cada operación mediante un código de
  salida que distinga entre ejecución correcta, ausencia de resultados y error.
- **FR-022**: El sistema MUST NOT requerir autenticación, cuentas de usuario ni credenciales de
  ningún tipo, y MUST funcionar íntegramente en la terminal sin interfaz gráfica.
- **FR-023**: El sistema MUST funcionar de forma completamente local, sin depender de servicios
  remotos ni de conexión a la red.
- **FR-024**: Cada capacidad de la herramienta (crear, listar, buscar y exportar) MUST contar con
  pruebas automatizadas que cubran tanto el camino de éxito como los caminos de error, y las
  pruebas MUST NOT depender de servicios externos ni de la red.
- **FR-025**: El sistema MUST NOT incorporar dependencias de terceros que no hayan sido
  justificadas y aprobadas previamente.

### Key Entities

- **Nota**: el registro central del producto. Se identifica de forma única y contiene un título
  (obligatorio), un contenido de texto (opcional), una fecha y hora de creación, y sus etiquetas.
  Es la unidad que el usuario crea, lista, busca y exporta.
- **Etiqueta**: el mecanismo de clasificación del usuario. Es un texto corto que se normaliza
  antes de guardarse y que se asocia a una o varias notas. Varias notas pueden compartir la
  misma etiqueta, y una nota puede no tener ninguna.
- **Resultado de exportación**: el archivo Markdown generado a partir de un conjunto de notas. Es
  un resultado derivado, no un registro almacenado; no vuelve a formar parte de las notas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario que acaba de instalar la herramienta puede crear su primera nota
  completa (título, contenido y etiquetas) en menos de 1 minuto desde la terminal.
- **SC-002**: Un usuario sin documentación puede completar el recorrido crear → listar → buscar
  por etiqueta en menos de 5 minutos sin ayuda externa.
- **SC-003**: El 100% de las notas existentes aparecen en el listado, sin omisiones ni
  duplicados, verificado sobre un conjunto de 500 notas.
- **SC-004**: El listado de 500 notas se completa en menos de 3 segundos en un equipo de
  sobremesa de referencia.
- **SC-005**: El 100% de las notas devueltas por una búsqueda cumplen la condición de
  coincidencia de etiqueta, verificado sobre un conjunto de notas con combinaciones de etiquetas
  solapadas.
- **SC-006**: La exportación de 500 notas produce un archivo Markdown que contiene el 100% de las
  notas, con su título, fecha, etiquetas y contenido, y sin corrupción de caracteres.
- **SC-007**: La herramienta ejecuta 0 operaciones destructivas sobre el almacén de datos en su
  funcionamiento normal, verificado sobre la traza completa de las acciones del usuario.
- **SC-008**: El 100% de las capacidades de la herramienta (crear, listar, buscar y exportar)
  cuentan con pruebas automatizadas que pasan de forma repetida y sin acceso a la red.
- **SC-009**: El 95% de las ejecuciones terminan sin errores no explicados; todos los errores
  mostrados indican la causa y la acción correctiva en lenguaje comprensible.
- **SC-010**: La herramienta es utilizable de principio a fin por una sola persona en su terminal
  local, sin cuentas, sin servidor y sin conexión a la red.

## Assumptions

- **Actor único y local**: la herramienta la usa una sola persona en su propio equipo; no hay
  usuarios simultáneos ni necesidad de compartir el mismo almacén de notas entre personas.
- **Almacenamiento local**: la descripción de entrada indica SQLite como motor de almacenamiento;
  se conserva como restricción del producto. La ruta concreta del archivo está pendiente de
  confirmación (ver FR-003).
- **Sin autenticación**: por indicación explícita de la entrada, no habrá cuentas, contraseñas,
  sesiones ni ningún mecanismo de identidad.
- **Interfaz exclusivamente de terminal**: no habrá interfaz gráfica, panel web, escritorio ni
  integración con editores, tal como indica la entrada.
- **Funcionalidad fuera de alcance para la v1**: la edición y el borrado de notas existentes, la
  búsqueda por texto libre dentro del contenido, las categorías adicionales (por ejemplo `bug`,
  `command`, `idea`), el adjuntado de archivos o imágenes, la sincronización en la nube, el
  formato de exportación distinto de Markdown y cualquier forma de compartición o publicación
  automática. Su incorporación requerirá una ampliación explícita del alcance (Principio V de la
  Constitución).
- **Alcance de la búsqueda**: la búsqueda se define en torno a las etiquetas; el detalle de
  coincidencia exacta o parcial y la combinación de varias etiquetas está pendiente de
  confirmación (ver FR-010).
- **Etiquetas**: se asume un modelo de etiquetas libres sin jerarquías ni colores, y sin
 vocabulario predefinido que restrinja lo que el usuario puede escribir.
- **Formato de fecha**: las fechas se muestran al usuario en un formato local legible, con año,
  mes, día, hora y minutos.
- **Idioma de la interfaz**: la herramienta se comunica con el usuario en español, coherente con
  el idioma de trabajo del proyecto.
- **Sin red**: no se hablará con servicios remotos; la herramienta opera sin conexión.
- **Integridad ante fallos**: ante un error de almacenamiento, la herramienta nunca borra ni
  reconstruye el archivo de datos por su cuenta; informa del problema y deja los datos intactos
  (Principio II de la Constitución).
