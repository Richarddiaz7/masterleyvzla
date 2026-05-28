<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Máster Ley Vzla IA</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <!-- Firebase SDKs (CDN) -->
    <script src="https://www.gstatic.com/firebasejs/9.22.2/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.2/firebase-firestore-compat.js"></script>
    <style>
        :root {
            --bg: #0f172a;
            --card: #1e293b;
            --accent: #f59e0b;
            --text: #e2e8f0;
            --muted: #94a3b8;
            --success: #10b981;
            --danger: #ef4444;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 16px;
            line-height: 1.5;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .header h1 { font-size: 24px; color: var(--accent); }
        .card {
            background: var(--card);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 14px;
            border: 1px solid #334155;
            cursor: pointer;
            transition: .2s;
        }
        .card:active { transform: scale(0.98); }
        .card h2 { color: var(--accent); font-size: 18px; margin-bottom: 6px; }
        .card p { color: var(--muted); font-size: 14px; }
        .button {
            display: block;
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
        }
        .btn-primary { background: var(--accent); color: #0f172a; }
        .btn-secondary { background: #334155; color: var(--text); }
        .opciones {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 14px 0;
        }
        .opcion {
            padding: 16px;
            background: var(--card);
            border: 2px solid #334155;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            transition: .2s;
        }
        .opcion.correct { border-color: var(--success); background: #064e3b; }
        .opcion.incorrect { border-color: var(--danger); background: #7f1d1d; }
        .explicacion {
            background: #1e293b;
            padding: 12px;
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            margin-top: 12px;
            color: var(--muted);
            font-size: 14px;
        }
        .progress {
            height: 6px;
            background: #334155;
            border-radius: 3px;
            margin: 8px 0;
        }
        .progress-fill {
            height: 6px;
            background: var(--accent);
            border-radius: 3px;
            transition: .3s;
        }
        .hidden { display: none; }
        .badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-gratis { background: #334155; }
        .badge-premium { background: var(--accent); color: #0f172a; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚖️ Máster Ley Vzla IA</h1>
        <p>Practica Derecho Constitucional con casos reales</p>
    </div>

    <div id="temasScreen">
        <div class="card">
            <h2>📚 Elige un tema</h2>
            <p>Selecciona un artículo constitucional</p>
        </div>
        <div id="temasContainer"></div>
    </div>

    <div id="preguntaScreen" class="hidden">
        <div class="card">
            <h2 id="enunciado"></h2>
        </div>
        <div class="opciones" id="opcionesContainer"></div>
        <div id="explicacion" class="explicacion hidden"></div>
        <button id="btnSiguiente" class="button btn-primary hidden" onclick="cargarPregunta()">Siguiente ▶</button>
        <button class="button btn-secondary" onclick="volverTemas()">⬅ Volver</button>
    </div>

    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span>Retos hoy: <span id="retosHoy">0</span>/3</span>
            <span id="badgeCuenta"></span>
        </div>
        <div class="progress"><div class="progress-fill" id="progresoFill"></div></div>
    </div>

    <script>
        // --------------------------------------
        // CONFIGURACIÓN DE FIREBASE
        // --------------------------------------
        const firebaseConfig = {
            apiKey: "AIzaSyCOecJaAR2WJ8MW-WRSEqoxUYGEgxenxK8",
            authDomain: "masterleyvzla.firebaseapp.com",
            projectId: "masterleyvzla",
            storageBucket: "masterleyvzla.firebasestorage.app",
            messagingSenderId: "178092366571",
            appId: "1:178092366571:web:1c64f7cc911ceb6778bcae",
            measurementId: "G-YV5TFKLBLQ"
        };

        firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        // --------------------------------------
        // VARIABLES GLOBALES
        // --------------------------------------
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        let usuarioId = tg.initDataUnsafe?.user?.id ? String(tg.initDataUnsafe.user.id) : 'demo_user';
        let usuarioData = {};
        let preguntaActual = null;

        // --------------------------------------
        // FUNCIONES DE USUARIO
        // --------------------------------------
        async function cargarUsuario() {
            const fechaHoy = new Date().toISOString().split('T')[0];
            const userRef = db.collection('usuarios').doc(usuarioId);
            const doc = await userRef.get();

            if (!doc.exists) {
                // Crear usuario nuevo
                await userRef.set({
                    nombre: tg.initDataUnsafe?.user?.first_name || 'Estudiante',
                    tipo_cuenta: 'GRATIS',
                    retos_respondidos_hoy: 0,
                    ultimo_acceso: fechaHoy,
                    tema_actual: null,
                    rol: 'usuario'
                });
                usuarioData = (await userRef.get()).data();
            } else {
                usuarioData = doc.data();
                if (usuarioData.ultimo_acceso !== fechaHoy) {
                    await userRef.update({
                        retos_respondidos_hoy: 0,
                        ultimo_acceso: fechaHoy
                    });
                    usuarioData.retos_respondidos_hoy = 0;
                    usuarioData.ultimo_acceso = fechaHoy;
                }
            }
            actualizarUI();
        }

        function actualizarUI() {
            const retos = usuarioData.retos_respondidos_hoy || 0;
            document.getElementById('retosHoy').textContent = retos;
            document.getElementById('progresoFill').style.width = Math.min((retos / 3) * 100, 100) + '%';
            const badge = document.getElementById('badgeCuenta');
            badge.innerHTML = usuarioData.tipo_cuenta === 'PREMIUM' ?
                '<span class="badge badge-premium">PREMIUM</span>' :
                '<span class="badge badge-gratis">GRATIS</span>';
        }

        async function incrementarRetos() {
            const userRef = db.collection('usuarios').doc(usuarioId);
            await userRef.update({
                retos_respondidos_hoy: firebase.firestore.FieldValue.increment(1)
            });
            usuarioData.retos_respondidos_hoy++;
            actualizarUI();
        }

        // --------------------------------------
        // CARGAR TEMAS DESDE FIRESTORE
        // --------------------------------------
        async function cargarTemas() {
            const snapshot = await db.collection('articulos').orderBy('numero', 'asc').get();
            const temas = [];
            snapshot.forEach(doc => temas.push({ id: doc.id, ...doc.data() }));
            document.getElementById('temasContainer').innerHTML = temas.map(t => `
                <div class="card" onclick="seleccionarTema('${t.id}')">
                    <h2>📘 Art. ${t.numero || t.id}</h2>
                    <p>${t.titulo}</p>
                </div>
            `).join('');
        }

        async function seleccionarTema(articuloId) {
            const userRef = db.collection('usuarios').doc(usuarioId);
            await userRef.update({ tema_actual: Number(articuloId) });
            usuarioData.tema_actual = Number(articuloId);

            // Verificar límite
            if (usuarioData.tipo_cuenta === 'GRATIS' && usuarioData.retos_respondidos_hoy >= 3) {
                alert('⚠️ Límite de 3 retos gratuitos alcanzado. Pásate a PREMIUM.');
                return;
            }
            cargarPregunta();
        }

        // --------------------------------------
        // CARGAR PREGUNTA ALEATORIA
        // --------------------------------------
        async function cargarPregunta() {
            if (!usuarioData.tema_actual) {
                alert('Selecciona un tema primero.');
                volverTemas();
                return;
            }
            const preguntasRef = db.collection('preguntas')
                .where('articulo_id', '==', usuarioData.tema_actual);
            const snapshot = await preguntasRef.get();
            if (snapshot.empty) {
                alert('No hay preguntas para este tema aún.');
                volverTemas();
                return;
            }
            const preguntas = [];
            snapshot.forEach(doc => preguntas.push({ id: doc.id, ...doc.data() }));
            const randomIndex = Math.floor(Math.random() * preguntas.length);
            preguntaActual = preguntas[randomIndex];

            document.getElementById('temasScreen').classList.add('hidden');
            document.getElementById('preguntaScreen').classList.remove('hidden');
            document.getElementById('enunciado').textContent = preguntaActual.enunciado;
            const opciones = ['A', 'B', 'C', 'D'];
            document.getElementById('opcionesContainer').innerHTML = opciones.map(l => `
                <div class="opcion" id="op_${l}" onclick="responder('${l}')">${l}) ${preguntaActual['opcion_' + l.toLowerCase()]}</div>
            `).join('');
            document.getElementById('explicacion').classList.add('hidden');
            document.getElementById('btnSiguiente').classList.add('hidden');
        }

        // --------------------------------------
        // RESPONDER Y ACTUALIZAR CONTADOR
        // --------------------------------------
        async function responder(letra) {
            document.querySelectorAll('.opcion').forEach(o => o.style.pointerEvents = 'none');
            const correcta = preguntaActual.respuesta_correcta;
            const esCorrecta = (letra === correcta);

            document.getElementById('op_' + correcta).classList.add('correct');
            if (!esCorrecta) {
                document.getElementById('op_' + letra).classList.add('incorrect');
            }
            document.getElementById('explicacion').textContent = '💡 ' + preguntaActual.explicacion;
            document.getElementById('explicacion').classList.remove('hidden');
            document.getElementById('btnSiguiente').classList.remove('hidden');

            // Incrementar contador si es GRATIS
            if (usuarioData.tipo_cuenta === 'GRATIS') {
                await incrementarRetos();
            }
        }

        function volverTemas() {
            document.getElementById('temasScreen').classList.remove('hidden');
            document.getElementById('preguntaScreen').classList.add('hidden');
            preguntaActual = null;
            cargarTemas();
        }

        // --------------------------------------
        // INICIALIZACIÓN
        // --------------------------------------
        cargarUsuario();
        cargarTemas();
    </script>
</body>
</html>
