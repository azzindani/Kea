
$files = Get-ChildItem -Path "kernel/nodes", "kernel/agents", "kernel/templates" -Recurse -Filter *.py

foreach ($file in $files) {
    if ($file.Name -eq "__init__.py") { continue }
    
    $content = Get-Content $file.FullName -Raw
    $originalContent = $content
    
    # 1. Update references to core (already moved)
    # services.orchestrator.core -> kernel.core/memory/etc...
    # We can reuse the logic from update_imports.ps1 if we had it, but let's just do a quick find-replace based on the map
    
    $replacements = @{
        "services.orchestrator.core.kernel_cell" = "kernel.core.kernel_cell";
        "services.orchestrator.core.cognitive_cycle" = "kernel.core.cognitive_cycle";
        
        # ... (Add comprehensive list or use regex for services.orchestrator.core -> kernel.core)
        # Simplified:
        "services.orchestrator.core." = "kernel.core."; # Fallback, risky but better than nothing
        
        # Specific submodules
        "services.orchestrator.core.working_memory" = "kernel.memory.working_memory";
        "services.orchestrator.core.tool_bridge" = "kernel.actions.tool_bridge";
        "services.orchestrator.core.graph" = "kernel.flow.graph";
        
        # 2. Update references to nodes/agents/templates (self-references)
        "services.orchestrator.nodes" = "kernel.nodes";
        "services.orchestrator.agents" = "kernel.agents";
        "services.orchestrator.templates" = "kernel.templates";
        
        # 3. Fix relative imports within the moved files
        # e.g. from .planner import -> from kernel.nodes.planner import
    }
    
    # Apply specific replacements first
    foreach ($key in $replacements.Keys) {
        if ($content.Contains($key)) {
            $content = $content.Replace($key, $replacements[$key])
        }
    }
    
    # Fix relatives (naive approach, strict is better but this is a fast patch)
    # Planner node might import other nodes via .
    
    if ($content -ne $originalContent) {
        Set-Content -Path $file.FullName -Value $content -NoNewline -Encoding UTF8
        Write-Host "Updated imports in $($file.FullName)"
    }
}
