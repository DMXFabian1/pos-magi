# Establecer la ruta raíz del proyecto
$projectRoot = Get-Location

# Archivo de salida para guardar la estructura
$outputFile = Join-Path $projectRoot "structure.txt"

# Función para listar recursivamente las carpetas y archivos
function List-FolderStructure {
    param (
        [string]$path,
        [int]$indentLevel = 0
    )

    # Obtener todos los elementos (carpetas y archivos) en la ruta actual
    $items = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Sort-Object { $_.PSIsContainer -eq $false }

    foreach ($item in $items) {
        # Crear la indentación para mostrar la jerarquía
        $indent = "  " * $indentLevel
        $itemPath = $item.FullName.Replace($projectRoot, ".")

        if ($item.PSIsContainer) {
            # Es una carpeta
            $line = "$indent📁 $itemPath"
            Write-Output $line
            $line | Out-File -FilePath $outputFile -Append -Encoding utf8
            # Llamada recursiva para listar el contenido de la carpeta
            List-FolderStructure -path $item.FullName -indentLevel ($indentLevel + 1)
        } else {
            # Es un archivo
            $line = "$indent📄 $itemPath"
            Write-Output $line
            $line | Out-File -FilePath $outputFile -Append -Encoding utf8
        }
    }
}

# Limpiar el archivo de salida si ya existe
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}

# Iniciar el listado desde la raíz del proyecto
Write-Output "=== Estructura de Carpetas y Archivos en $projectRoot ==="
Write-Output "=== Estructura de Carpetas y Archivos en $projectRoot ===" | Out-File -FilePath $outputFile -Encoding utf8
List-FolderStructure -path $projectRoot

# Mostrar mensaje final
Write-Output "✔ Estructura generada. Revisa 'structure.txt' para más detalles."