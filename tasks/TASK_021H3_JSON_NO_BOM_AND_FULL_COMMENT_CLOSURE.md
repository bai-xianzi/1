# TASK_021H3 Encoding repair and full comment closure

- Convert tracked PowerShell source to UTF-8 with BOM for Windows PowerShell 5.1.
- Preserve decoded source text and existing newline characters.
- Validate every file with the local PowerShell parser.
- Run the full teaching-comment closure only after all PowerShell source parses.
- Do not execute project verification scripts or database write paths during repair.
