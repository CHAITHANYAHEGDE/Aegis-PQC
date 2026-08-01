import re

with open("/Users/chaithanyahegde/Downloads/aegis-pqc-hero.html", "r") as f:
    hero = f.read()

with open("/Users/chaithanyahegde/pqc_ai_shield/templates/index.html", "r") as f:
    dashboard = f.read()

# Extract styles
hero_styles = re.search(r"<style>(.*?)</style>", hero, re.DOTALL).group(1)
dash_styles = re.search(r"<style>(.*?)</style>", dashboard, re.DOTALL).group(1)

# Modify hero styles for fixed background
hero_styles = hero_styles.replace(
    "position:absolute; top:0; left:0;\n    width:100%; height:100%;",
    "position:fixed; top:0; left:0;\n    width:100%; height:100%;",
)
hero_styles = hero_styles.replace(
    ".noise-veil{\n    position:absolute; inset:0;",
    ".noise-veil{\n    position:fixed; inset:0;",
)
hero_styles = hero_styles.replace(
    ".binary-field{\n    position:absolute; inset:0;",
    ".binary-field{\n    position:fixed; inset:0;",
)
hero_styles = hero_styles.replace(
    ".vignette{\n    position:absolute; inset:0;",
    ".vignette{\n    position:fixed; inset:0;",
)
# Hero UI shouldn't be absolute anymore if we want it to flow, or we make it relative with 100vh
hero_styles = hero_styles.replace(
    ".hero-ui{\n    position:absolute; inset:0;",
    ".hero-ui{\n    position:relative; width:100%; height:100vh;",
)

# Remove conflicting body styles from dashboard
dash_styles = re.sub(r"body\s*{[^}]+}", "", dash_styles)

# Extract scripts
hero_script = re.search(r"<script>(.*?)</script>", hero, re.DOTALL).group(1)
dash_script = re.search(r"<script>(.*?)</script>", dashboard, re.DOTALL).group(1)

# Extract HTML parts
hero_html = re.search(
    r'<div id="app">(.*?)</div>\s*<script src', hero, re.DOTALL
).group(1)
dash_html = re.search(r"<main>(.*?)</main>", dashboard, re.DOTALL).group(1)

merged = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aegis-PQC: Neural Side-Channel Guard</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {hero_styles}
        {dash_styles}
        
        main {{
            position: relative;
            z-index: 10;
            background: linear-gradient(to bottom, rgba(3,3,8,0) 0%, rgba(3,3,8,1) 20%);
            padding-top: 5rem;
        }}
    </style>
</head>
<body>
    <div id="app">
        {hero_html}
    </div>
    
    <main>
        {dash_html}
    </main>
    
    <script>
        {hero_script}
        {dash_script}
        // Initialize dashboard
        window.addEventListener('load', () => {{
            initChart();
            fetchStats();
        }});
    </script>
</body>
</html>
"""

with open("/Users/chaithanyahegde/pqc_ai_shield/templates/index.html", "w") as f:
    f.write(merged)
