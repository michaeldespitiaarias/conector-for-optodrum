"""Spanish interface text for OptoDrum Connector (see i18n.py).

Keys are the English text exactly as the source writes it. Entries that
format values keep the same {placeholders}. PATTERNS translate messages
built at run time; their captured groups (column names, counts) pass
through unchanged.
"""

STRINGS = {
    'Light mode':
        'Claro',
    'Dark mode':
        'Oscuro',
    'Match system':
        'Según el sistema',
    'Match system follows the light or dark setting of your computer.':
        'Según el sistema sigue el ajuste claro u oscuro de tu ordenador.',
    'Settings':
        'Ajustes',
    'Language':
        'Idioma',
    'Appearance':
        'Apariencia',
    "All files": "Todos los archivos",
    "Back": "Atrás",
    "Browse…": "Examinar…",
    "Cancel": "Cancelar",
    "Choose a folder": "Elige una carpeta",
    "Choose the metadata file": "Elige el archivo de metadatos",
    "Close": "Cerrar",
    "Could not prepare the example:": "No se pudo preparar el ejemplo:",
    "Data folder": "Carpeta de datos",
    "Get started": "Empezar",
    "Getting started": "Primeros pasos",
    "Help": "Ayuda",
    "Metadata": "Metadatos",
    "No data at hand? Load an example project":
        "¿Sin datos a mano? Carga un proyecto de ejemplo",
    "Open folder": "Abrir carpeta",
    "Output": "Resultados",
    "Output folder": "Carpeta de resultados",
    "Project name": "Nombre del proyecto",
    "Starting…": "Iniciando…",
    "Tables (CSV / Excel / TSV)": "Tablas (CSV / Excel / TSV)",
    "What it is not": "Qué no es",
    "\"{folder}\" is not a folder.": "\"{folder}\" no es una carpeta.",
    "A small, standalone tool that turns OptoDrum's .summary staircase exports into one table, optodrum_report.csv: one row per animal and experiment, with the visual acuity threshold and the contrast sensitivity threshold at every spatial frequency tested.":
        "Una herramienta pequeña e independiente que convierte las exportaciones .summary de escalera de OptoDrum en una tabla, optodrum_report.csv: una fila por animal y experimento, con el umbral de agudeza visual y el umbral de sensibilidad al contraste en cada frecuencia espacial probada.",
    "An optional table (.csv, .xlsx or .txt) naming each animal's group. It is found automatically when it sits in the data folder; use Browse when it is somewhere else. Its first column is the Mouse ID, and every other column (Genotype, Gender, Group...) is added to the report for that animal. Changing the data folder clears the metadata found in the previous one.":
        "Una tabla opcional (.csv, .xlsx o .txt) que nombra el grupo de cada animal. Se encuentra automáticamente cuando está en la carpeta de datos; usa Examinar cuando está en otro lugar. Su primera columna es el Mouse ID, y cada una de las demás (Genotype, Gender, Group...) se añade al informe para ese animal. Cambiar la carpeta de datos borra los metadatos encontrados en la anterior.",
    "Cancelled": "Cancelado",
    "Convert OptoDrum exports": "Convertir exportaciones de OptoDrum",
    "Converting the exports": "Convirtiendo las exportaciones",
    "Every .summary file under the data folder, including folders inside it. A session whose test type is visualacuity is read as an ACUITY staircase; any other test type as a CONTRAST staircase. The count updates whenever the data folder changes, and Run stays unavailable while it is zero.":
        "Cada archivo .summary de la carpeta de datos, incluidas las carpetas que contiene. Una sesión cuyo tipo de prueba es visualacuity se lee como escalera ACUITY; cualquier otro tipo, como escalera CONTRAST. El recuento se actualiza cada vez que cambia la carpeta de datos, y Ejecutar no está disponible mientras sea cero.",
    "Every file found is read and combined into one row per animal and experiment. A contrast value of -1 is stored as 99.99 (below the detectable threshold); any other negative value is left empty. When the run finishes, the page shows how many rows were written and any files it had to skip, and Open folder shows optodrum_report.csv.":
        "Cada archivo encontrado se lee y se combina en una fila por animal y experimento. Un valor de contraste de -1 se guarda como 99.99 (por debajo del umbral detectable); cualquier otro valor negativo se deja vacío. Al terminar, la página indica cuántas filas se escribieron y qué archivos tuvo que omitir, y Abrir carpeta muestra optodrum_report.csv.",
    "Files found": "Archivos encontrados",
    "Input": "Entrada",
    "It performs no statistical analysis and draws no plots; it extracts "
    "and tabulates. optodrum_report.csv is an ordinary measurement table "
    "for any statistical or plotting software.":
        "No realiza análisis estadísticos ni gráficos; extrae y tabula. "
        "optodrum_report.csv es una tabla de medidas ordinaria para "
        "cualquier programa estadístico o de gráficos.",
    "No .summary files were found in this folder or the folders inside it.":
        "No se encontraron archivos .summary en esta carpeta ni en las carpetas que contiene.",
    "No results could be extracted, so no report was written.":
        "No se pudo extraer ningún resultado, así que no se escribió ningún informe.",
    "Optional. Found automatically when it sits in the data folder.":
        "Opcional. Se encuentra automáticamente cuando está en la carpeta de datos.",
    "OptoDrum Connector": "OptoDrum Connector",
    "OptoDrum staircase exports, one structured report":
        "Exportaciones de escalera de OptoDrum, un informe estructurado",
    "Output folder and project name":
        "Carpeta de resultados y nombre del proyecto",
    "Pick the data folder to begin.":
        "Elige la carpeta de datos para empezar.",
    "Pick the folder with the OptoDrum sessions and where the report goes, then press Run.":
        "Elige la carpeta con las sesiones de OptoDrum y dónde va el informe, y pulsa Ejecutar.",
    "Get started leads to the data folder holding the OptoDrum sessions, "
    "the output folder and the project name.":
        "Empezar conduce a la carpeta de datos con las sesiones de "
        "OptoDrum, la carpeta de salida y el nombre del proyecto.",
    "Reading {file}  ·  {current} of {total}":
        "Leyendo {file}  ·  {current} de {total}",
    "Report ready": "Informe listo",
    "Nothing to report": "Nada que informar",
    "Report written.": "Informe escrito.",
    "Run": "Ejecutar",
    "Set the output folder and a project name to run.":
        "Fija la carpeta de resultados y un nombre de proyecto para ejecutar.",
    "The conversion stopped": "La conversión se detuvo",
    "The folder holding the session subfolders, read as it is. Each "
    "session is a subfolder named "
    "<year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>. Files inside a "
    "folder whose name does not follow this pattern are skipped, and the "
    "run reports how many.":
        "La carpeta que contiene las subcarpetas de sesión, leída tal "
        "cual. Cada sesión es una subcarpeta con el nombre "
        "<year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>. Los archivos "
        "de una carpeta cuyo nombre no sigue este patrón se omiten, y el "
        "análisis indica cuántos.",
    "The report is written to Output folder, in a subfolder with this name.":
        "El informe se escribe en la carpeta de resultados, en una subcarpeta con este nombre.",
    "Together they decide where the report is written: {Output folder}/{Project name}/optodrum_report.csv. The project name is suggested from the data folder's name and can be changed freely.":
        "Juntos deciden dónde se escribe el informe: {Output folder}/{Project name}/optodrum_report.csv. El nombre del proyecto se propone a partir del nombre de la carpeta de datos y se puede cambiar libremente.",
    "What OptoDrum Connector is": "Qué es OptoDrum Connector",
    "What each control on this page does and how to use it.":
        "Qué hace cada control de esta página y cómo usarlo.",
    "the conversion stopped": "la conversión se detuvo",
    "{n} .summary file found": "{n} archivo .summary encontrado",
    "{n} .summary files found": "{n} archivos .summary encontrados",
    "{n} animal": "{n} animal",
    "{n} animals": "{n} animales",
    "{n} file could not be read": "{n} archivo no se pudo leer",
    "{n} files could not be read": "{n} archivos no se pudieron leer",
    "{n} file skipped: its folder name does not follow <year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>":
        "{n} archivo omitido: el nombre de su carpeta no sigue <year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>",
    "{n} files skipped: their folder names do not follow <year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>":
        "{n} archivos omitidos: los nombres de sus carpetas no siguen <year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>",
    "{n} row written": "{n} fila escrita",
    "{n} rows written": "{n} filas escritas",
}

# Messages built at run time. Groups pass through untranslated.
PATTERNS = []
