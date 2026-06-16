from flask import Flask, jsonify, render_template_string, request
from datetime import datetime
import os
import random

app = Flask(__name__)

INCIDENTS = [
    {
        "codename": "Deploy Fantasma",
        "level": "ALTO",
        "symptom": "La app funciona en local, pero en producción responde como si nadie viviera ahí.",
        "root": "Variables de entorno incompletas o nombre de imagen mal etiquetado.",
        "fixes": [
            "Validar secrets y variables antes del build.",
            "Publicar la imagen con tag latest y SHA del commit.",
            "Agregar endpoint /health para comprobar que el contenedor está vivo.",
        ],
        "commit": "fix: normalizar variables de entorno y tags de imagen",
    },
    {
        "codename": "Contenedor Zombi",
        "level": "MEDIO",
        "symptom": "El contenedor parece estar arriba, pero la aplicación no responde correctamente.",
        "root": "El puerto expuesto no coincide con el puerto usado por la app.",
        "fixes": [
            "Revisar EXPOSE del Dockerfile.",
            "Confirmar mapeo de puertos en docker-compose.yml.",
            "Ejecutar docker logs para leer el fallo real.",
        ],
        "commit": "chore: alinear puertos entre Flask, Dockerfile y Compose",
    },
    {
        "codename": "Build Envenenado",
        "level": "CRÍTICO",
        "symptom": "El workflow falla justo cuando intenta construir o subir la imagen.",
        "root": "Permisos insuficientes para publicar en GitHub Packages o login incorrecto en GHCR.",
        "fixes": [
            "Mantener permissions: packages: write en el workflow.",
            "Usar GITHUB_TOKEN para autenticarse contra ghcr.io.",
            "Convertir el nombre de la imagen a minúsculas antes de publicar.",
        ],
        "commit": "ci: corregir permisos de publicación en ghcr",
    },
    {
        "codename": "Rollback Ninja",
        "level": "BAJO",
        "symptom": "Una versión nueva rompe algo que antes funcionaba perfecto.",
        "root": "No existe una referencia clara a la versión anterior estable.",
        "fixes": [
            "Etiquetar imágenes con el SHA del commit.",
            "Guardar el último tag estable antes de desplegar.",
            "Documentar un comando de rollback rápido.",
        ],
        "commit": "ci: publicar imagen con tag latest y sha corto",
    },
]

LEVEL_POINTS = {"BAJO": 25, "MEDIO": 50, "ALTO": 75, "CRÍTICO": 95}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Caja Negra DevOps</title>
    <style>
        :root {
            --bg: #06080f;
            --panel: rgba(14, 18, 31, 0.84);
            --panel-strong: rgba(21, 27, 45, 0.94);
            --line: rgba(121, 255, 210, 0.18);
            --text: #edf7ff;
            --muted: #93a4ba;
            --accent: #3dffb5;
            --orange: #ff985f;
            --red: #ff5f7a;
            --blue: #72a7ff;
            --shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at 20% 15%, rgba(61, 255, 181, 0.16), transparent 28%),
                radial-gradient(circle at 85% 20%, rgba(114, 167, 255, 0.14), transparent 30%),
                radial-gradient(circle at 55% 90%, rgba(255, 152, 95, 0.12), transparent 32%),
                var(--bg);
            color: var(--text);
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            overflow-x: hidden;
        }

        .grid-bg {
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: 0.28;
            background-image:
                linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
            background-size: 44px 44px;
            mask-image: radial-gradient(circle at center, black, transparent 76%);
        }

        .shell {
            width: min(1180px, calc(100% - 32px));
            margin: 0 auto;
            padding: 42px 0;
            position: relative;
        }

        .hero {
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 24px;
            align-items: stretch;
        }

        .card {
            border: 1px solid var(--line);
            background: var(--panel);
            border-radius: 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(20px);
        }

        .intro {
            padding: 36px;
            position: relative;
            overflow: hidden;
        }

        .intro::after {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: rgba(61, 255, 181, 0.12);
            filter: blur(6px);
            right: -70px;
            top: -70px;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 999px;
            color: var(--accent);
            border: 1px solid rgba(61, 255, 181, 0.24);
            background: rgba(61, 255, 181, 0.08);
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
        }

        .pulse {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: var(--accent);
            box-shadow: 0 0 0 0 rgba(61, 255, 181, 0.8);
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            70% { box-shadow: 0 0 0 14px rgba(61, 255, 181, 0); }
            100% { box-shadow: 0 0 0 0 rgba(61, 255, 181, 0); }
        }

        h1 {
            margin: 28px 0 14px;
            font-size: clamp(2.8rem, 7vw, 6.6rem);
            line-height: 0.88;
            letter-spacing: -0.08em;
        }

        h1 span {
            display: block;
            color: transparent;
            -webkit-text-stroke: 1px rgba(237, 247, 255, 0.7);
        }

        .lead {
            max-width: 680px;
            color: var(--muted);
            font-size: 1.08rem;
            line-height: 1.7;
            margin: 0 0 28px;
        }

        .actions {
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
        }

        button, select, input {
            font: inherit;
        }

        .btn {
            border: 0;
            border-radius: 16px;
            padding: 14px 18px;
            cursor: pointer;
            font-weight: 850;
            color: #06100d;
            background: linear-gradient(135deg, var(--accent), #a8ffe1);
            box-shadow: 0 14px 28px rgba(61, 255, 181, 0.18);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 34px rgba(61, 255, 181, 0.26);
        }

        .btn.secondary {
            color: var(--text);
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.06);
            box-shadow: none;
        }

        .terminal {
            min-height: 480px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .terminal-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 18px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.09);
            background: rgba(0,0,0,0.18);
        }

        .dots { display: flex; gap: 8px; }
        .dots i {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--red);
            display: block;
        }
        .dots i:nth-child(2) { background: var(--orange); }
        .dots i:nth-child(3) { background: var(--accent); }

        .terminal-title {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .console {
            padding: 22px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
            line-height: 1.7;
            color: #cfe9dd;
            flex: 1;
            background:
                linear-gradient(rgba(61,255,181,0.045) 50%, transparent 50%) 0 0 / 100% 6px,
                rgba(2, 7, 11, 0.56);
        }

        .console p { margin: 0 0 10px; }
        .console .ok { color: var(--accent); }
        .console .warn { color: var(--orange); }
        .console .danger { color: var(--red); }
        .console .muted { color: #6f8296; }

        .workspace {
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 24px;
            margin-top: 24px;
        }

        .panel { padding: 24px; }
        .panel h2 {
            margin: 0 0 8px;
            font-size: 1.35rem;
            letter-spacing: -0.03em;
        }
        .panel p { color: var(--muted); line-height: 1.6; }

        .field { margin: 18px 0; }
        .field label {
            display: block;
            color: #c9d8e8;
            font-weight: 800;
            font-size: 0.9rem;
            margin-bottom: 8px;
        }
        .field select, .field input {
            width: 100%;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.06);
            color: var(--text);
            border-radius: 14px;
            padding: 13px 14px;
            outline: none;
        }
        option { color: #111827; }

        .result {
            min-height: 420px;
            padding: 0;
            overflow: hidden;
        }

        .result-head {
            padding: 24px;
            background: linear-gradient(135deg, rgba(61,255,181,0.14), rgba(114,167,255,0.08));
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .badges {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }

        .badge {
            border: 1px solid rgba(255,255,255,0.14);
            background: rgba(0,0,0,0.18);
            border-radius: 999px;
            padding: 8px 11px;
            color: #d7e7f7;
            font-size: 0.82rem;
            font-weight: 800;
        }

        .result-body {
            display: grid;
            grid-template-columns: 0.8fr 1.2fr;
            gap: 18px;
            padding: 24px;
        }

        .meter {
            aspect-ratio: 1 / 1;
            display: grid;
            place-items: center;
            border-radius: 28px;
            background:
                conic-gradient(var(--accent) var(--value), rgba(255,255,255,0.08) 0),
                rgba(255,255,255,0.04);
            position: relative;
        }
        .meter::after {
            content: "";
            position: absolute;
            inset: 20px;
            background: var(--panel-strong);
            border-radius: 22px;
        }
        .meter-content {
            position: relative;
            z-index: 1;
            text-align: center;
        }
        .meter strong {
            font-size: 3.2rem;
            letter-spacing: -0.08em;
        }
        .meter span {
            display: block;
            color: var(--muted);
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.74rem;
        }

        .diagnosis h3 {
            margin: 0 0 8px;
            color: #ffffff;
        }
        .diagnosis p { margin: 0 0 16px; }
        .fix-list {
            display: grid;
            gap: 10px;
            margin: 12px 0 0;
        }
        .fix {
            border-left: 3px solid var(--accent);
            background: rgba(255,255,255,0.045);
            padding: 12px 14px;
            border-radius: 12px;
            color: #dcecff;
        }

        .copybox {
            margin-top: 18px;
            padding: 14px;
            border-radius: 14px;
            border: 1px dashed rgba(255,255,255,0.16);
            background: rgba(0,0,0,0.18);
            color: #bfe8d8;
            font-family: "SFMono-Regular", Consolas, monospace;
            word-break: break-word;
        }

        @media (max-width: 920px) {
            .hero, .workspace, .result-body { grid-template-columns: 1fr; }
            .terminal { min-height: auto; }
            .intro { padding: 28px; }
            .shell { padding-top: 24px; }
        }
    </style>
</head>
<body>
    <div class="grid-bg"></div>
    <main class="shell">
        <section class="hero">
            <div class="card intro">
                <div class="eyebrow"><span class="pulse"></span> Docker + GitHub Actions + Packages</div>
                <h1>Caja Negra <span>DevOps</span></h1>
                <p class="lead">
                    Esta app ya no muestra un reloj. Ahora funciona como una mini cabina de diagnóstico:
                    simula incidentes de despliegue, genera una causa probable, propone acciones de rescate
                    y deja listo un mensaje de commit para documentar la solución.
                </p>
                <div class="actions">
                    <button class="btn" id="randomBtn">Generar incidente sorpresa</button>
                    <button class="btn secondary" id="cleanBtn">Reiniciar consola</button>
                </div>
            </div>

            <div class="card terminal">
                <div class="terminal-top">
                    <div class="dots"><i></i><i></i><i></i></div>
                    <div class="terminal-title">blackbox://pipeline-monitor</div>
                </div>
                <div class="console" id="console">
                    <p class="ok">$ docker build -t caja-negra-devops .</p>
                    <p class="muted">Imagen local preparada para simular incidentes.</p>
                    <p class="ok">$ github actions: build-and-push</p>
                    <p class="muted">Workflow listo para publicar el paquete en ghcr.io.</p>
                    <p class="warn">$ esperando señal del operador...</p>
                </div>
            </div>
        </section>

        <section class="workspace">
            <aside class="card panel">
                <h2>Analizador manual</h2>
                <p>Elige el estado de tu proyecto y la caja negra te devuelve un diagnóstico con estilo de postmortem.</p>

                <div class="field">
                    <label for="stage">Fase afectada</label>
                    <select id="stage">
                        <option value="build">Build / construcción de imagen</option>
                        <option value="deploy">Deploy / publicación</option>
                        <option value="runtime">Runtime / contenedor vivo</option>
                        <option value="rollback">Rollback / versión anterior</option>
                    </select>
                </div>

                <div class="field">
                    <label for="symptoms">Síntoma principal</label>
                    <select id="symptoms">
                        <option value="ghcr">No aparece el package en GitHub</option>
                        <option value="port">Localhost no carga</option>
                        <option value="secret">Fallan secrets o permisos</option>
                        <option value="works-local">Funciona local, falla al publicar</option>
                    </select>
                </div>

                <div class="field">
                    <label for="operator">Operador</label>
                    <input id="operator" value="Andrew" maxlength="24">
                </div>

                <button class="btn" id="analyzeBtn">Analizar señal</button>
            </aside>

            <section class="card result" id="result">
                <div class="result-head">
                    <div class="eyebrow"><span class="pulse"></span> Reporte generado</div>
                    <h2 id="incidentTitle">Sin incidente activo</h2>
                    <div class="badges" id="badges">
                        <span class="badge">Estado: en espera</span>
                        <span class="badge">Sistema: Flask</span>
                        <span class="badge">Puerto: 5000</span>
                    </div>
                </div>
                <div class="result-body">
                    <div class="meter" id="meter" style="--value: 12%;">
                        <div class="meter-content">
                            <strong id="riskValue">12</strong>
                            <span>riesgo</span>
                        </div>
                    </div>
                    <div class="diagnosis">
                        <h3 id="symptomTitle">La caja negra está limpia.</h3>
                        <p id="rootCause">Genera o analiza una señal para crear un reporte DevOps.</p>
                        <div class="fix-list" id="fixList">
                            <div class="fix">El workflow de GitHub Actions se mantiene para construir y publicar la imagen Docker.</div>
                            <div class="fix">El proyecto conserva Dockerfile, docker-compose y publicación hacia GitHub Packages.</div>
                        </div>
                        <div class="copybox" id="commitBox">commit sugerido: chore: iniciar caja negra devops</div>
                    </div>
                </div>
            </section>
        </section>
    </main>

    <script>
        const consoleBox = document.getElementById('console');
        const incidentTitle = document.getElementById('incidentTitle');
        const badges = document.getElementById('badges');
        const meter = document.getElementById('meter');
        const riskValue = document.getElementById('riskValue');
        const symptomTitle = document.getElementById('symptomTitle');
        const rootCause = document.getElementById('rootCause');
        const fixList = document.getElementById('fixList');
        const commitBox = document.getElementById('commitBox');

        function logLine(text, type = 'muted') {
            const p = document.createElement('p');
            p.className = type;
            p.textContent = text;
            consoleBox.appendChild(p);
            consoleBox.scrollTop = consoleBox.scrollHeight;
        }

        function renderReport(data) {
            incidentTitle.textContent = data.codename;
            badges.innerHTML = `
                <span class="badge">Nivel: ${data.level}</span>
                <span class="badge">Operador: ${data.operator}</span>
                <span class="badge">Fase: ${data.stage}</span>
                <span class="badge">Hora: ${data.generated_at}</span>
            `;
            meter.style.setProperty('--value', `${data.risk}%`);
            riskValue.textContent = data.risk;
            symptomTitle.textContent = data.symptom;
            rootCause.textContent = data.root;
            fixList.innerHTML = data.fixes.map(item => `<div class="fix">${item}</div>`).join('');
            commitBox.textContent = `commit sugerido: ${data.commit}`;

            logLine(`$ blackbox scan --stage ${data.stage}`, 'ok');
            logLine(`incidente detectado: ${data.codename}`, data.risk >= 80 ? 'danger' : 'warn');
            logLine(`riesgo calculado: ${data.risk}/100`, 'muted');
            logLine(`siguiente acción: ${data.fixes[0]}`, 'ok');
        }

        async function fetchRandom() {
            const res = await fetch('/api/incidente/aleatorio');
            const data = await res.json();
            renderReport(data);
        }

        async function analyzeSignal() {
            const payload = {
                stage: document.getElementById('stage').value,
                symptoms: document.getElementById('symptoms').value,
                operator: document.getElementById('operator').value || 'Operador'
            };
            const res = await fetch('/api/incidente/analizar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            renderReport(data);
        }

        document.getElementById('randomBtn').addEventListener('click', fetchRandom);
        document.getElementById('analyzeBtn').addEventListener('click', analyzeSignal);
        document.getElementById('cleanBtn').addEventListener('click', () => {
            consoleBox.innerHTML = `
                <p class="ok">$ systemctl restart blackbox-devops</p>
                <p class="muted">Consola reiniciada. Señal limpia.</p>
                <p class="warn">$ esperando nueva anomalía...</p>
            `;
        });
    </script>
</body>
</html>
"""


def build_report(base_incident, stage="auto", operator="Andrew", symptom_key="random"):
    risk = LEVEL_POINTS.get(base_incident["level"], 50) + random.randint(-6, 6)
    risk = max(10, min(99, risk))
    return {
        "codename": base_incident["codename"],
        "level": base_incident["level"],
        "stage": stage,
        "operator": operator.strip()[:24] or "Operador",
        "symptom_key": symptom_key,
        "symptom": base_incident["symptom"],
        "root": base_incident["root"],
        "fixes": base_incident["fixes"],
        "commit": base_incident["commit"],
        "risk": risk,
        "generated_at": datetime.now().strftime("%H:%M:%S"),
    }


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "caja-negra-devops"})


@app.route("/api/incidente/aleatorio")
def random_incident():
    incident = random.choice(INCIDENTS)
    return jsonify(build_report(incident))


@app.route("/api/incidente/analizar", methods=["POST"])
def analyze_incident():
    data = request.get_json(silent=True) or {}
    stage = data.get("stage", "auto")
    symptom_key = data.get("symptoms", "random")
    operator = data.get("operator", "Andrew")

    stage_map = {
        "build": "Build Envenenado",
        "deploy": "Deploy Fantasma",
        "runtime": "Contenedor Zombi",
        "rollback": "Rollback Ninja",
    }
    symptom_map = {
        "ghcr": "Build Envenenado",
        "port": "Contenedor Zombi",
        "secret": "Build Envenenado",
        "works-local": "Deploy Fantasma",
    }

    target = symptom_map.get(symptom_key) or stage_map.get(stage)
    incident = next((item for item in INCIDENTS if item["codename"] == target), random.choice(INCIDENTS))
    return jsonify(build_report(incident, stage=stage, operator=operator, symptom_key=symptom_key))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)