// Web Worker: loads Pyodide, unpacks the game bundle, and runs FishE's Python
// game loop in the player's own browser.
//
// Communication with the main thread:
//   main → worker:  { type: 'init', sab: SharedArrayBuffer }
//   worker → main:  { type: 'status', msg: string }
//                   { type: 'ready' }
//                   { type: 'error', msg: string }
//                   { type: 'save', files: { path: content, ... } }
//                   string — a JSON {"type":"screen","screen":{...}} frame
//                            posted by PyodideUserInterface
//
// The player's responses arrive the other way, through the SharedArrayBuffer
// ring buffer the main thread writes into (see web/index.html). They cannot
// come over postMessage: FishE's game loop is synchronous, so it blocks the
// Worker while waiting for input, and a blocked Worker never runs onmessage.
//
// ── Why IndexedDB writes live on the main thread ─────────────────────────────
// Pyodide's build uses Atomics.wait() for time.sleep() when SharedArrayBuffer
// is available, which blocks the Worker's JS event loop entirely — so IDB
// callbacks (macrotasks) can never fire while Python is running. Instead the
// Worker walks /saves synchronously and postMessages the file map to the main
// thread, which writes to IDB from its own, unblocked, event loop. The initial
// restore still happens here in the Worker because it runs before Python
// starts, when nothing is blocking the event loop yet.

importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.0/full/pyodide.js');

const SAVE_DIRECTORY = '/saves';

const IDB_NAME    = 'fishe-saves';
const IDB_STORE   = 'files';
const IDB_VERSION = 1;

function idbOpen() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(IDB_NAME, IDB_VERSION);
        req.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains(IDB_STORE)) {
                db.createObjectStore(IDB_STORE);
            }
        };
        req.onsuccess = (e) => resolve(e.target.result);
        req.onerror   = (e) => reject(e.target.error);
    });
}

// ── Save restore: read IndexedDB into /saves before Python starts ────────────
// Always resolves, never rejects: a browser that won't hand back stored data
// should start the player on a fresh save file, not refuse to load the game.
async function loadSavesFromIDB(pyodide) {
    try {
        const db = await Promise.race([
            idbOpen(),
            new Promise((_, rej) =>
                setTimeout(() => rej(new Error('IndexedDB open timed out')), 5000)
            ),
        ]);

        const entries = await new Promise((resolve, reject) => {
            const result = [];
            let tx, cursorReq;
            try {
                tx        = db.transaction(IDB_STORE, 'readonly');
                cursorReq = tx.objectStore(IDB_STORE).openCursor();
            } catch (e) { reject(e); return; }
            cursorReq.onsuccess = (ev) => {
                const c = ev.target.result;
                if (c) { result.push({ path: c.key, content: c.value }); c.continue(); }
                else   resolve(result);
            };
            cursorReq.onerror = () => reject(cursorReq.error);
            tx.onerror        = () => reject(tx.error);
            tx.onabort        = () => reject(new Error('IndexedDB transaction aborted'));
        });

        let restored = 0;
        for (const { path, content } of entries) {
            // Save slots are directories (/saves/slot_1/player.json), so the
            // parents have to exist before the file can be written.
            const parts = path.split('/').filter(Boolean);
            let dir = '';
            for (let i = 0; i < parts.length - 1; i++) {
                dir += '/' + parts[i];
                try { pyodide.FS.mkdir(dir); } catch {}  // already there: fine
            }
            try {
                pyodide.FS.writeFile(path, content, { encoding: 'utf8' });
                restored++;
            } catch (e) {
                console.warn('[fishe] could not restore save file', path, e);
            }
        }
        if (restored > 0) console.log(`[fishe] ${restored} save file(s) restored`);
        try { db.close(); } catch {}

    } catch (err) {
        console.warn('[fishe] save restore skipped (starting fresh):', err);
    }
}

// ── Save flush: collect /saves and hand it to the main thread ────────────────
// Installed as globalThis.syncSaves, which src/browserSaveSync.py calls after
// every write or delete. Walking pyodide.FS is pure JavaScript and needs no
// event loop, and postMessage is synchronous from the Worker's side — so this
// works even though Python is mid-call and the Worker is otherwise blocked.

function makeSyncSaves(pyodide) {
    return () => {
        const files = {};
        function walk(path) {
            let entries;
            try { entries = pyodide.FS.readdir(path); } catch { return; }
            for (const name of entries) {
                if (name === '.' || name === '..') continue;
                const full = `${path}/${name}`;
                let stat;
                try { stat = pyodide.FS.stat(full); } catch { continue; }
                const isDirectory = (stat.mode & 0o170000) === 0o040000;
                if (isDirectory) {
                    walk(full);
                } else {
                    // FishE's saves are JSON, so UTF-8 is the whole story here.
                    try {
                        files[full] = pyodide.FS.readFile(full, { encoding: 'utf8' });
                    } catch (e) {
                        console.warn('[fishe] could not read save file', full, e);
                    }
                }
            }
        }
        walk(SAVE_DIRECTORY);
        self.postMessage({ type: 'save', files });
    };
}

// ── Worker entry point ───────────────────────────────────────────────────────

self.onmessage = async (e) => {
    if (e.data.type !== 'init') return;

    const { sab } = e.data;
    // [0] = write index, [1] = read index, both monotonically increasing and
    // taken modulo the ring size when indexing into the data region.
    globalThis.sabMeta     = new Int32Array(sab, 0, 2);
    globalThis.sabData     = new Uint8Array(sab, 8, e.data.ringSize);
    globalThis.sabRingSize = e.data.ringSize;
    globalThis.sendToMain  = (data) => self.postMessage(data);

    try {
        self.postMessage({ type: 'status', msg: 'Loading Python runtime…' });

        const pyodide = await loadPyodide({
            stdout: (msg) => console.log('[fishe]', msg),
            stderr: (msg) => console.warn('[fishe]', msg),
        });

        self.postMessage({ type: 'status', msg: 'Restoring saved games…' });

        pyodide.FS.mkdir(SAVE_DIRECTORY);
        await loadSavesFromIDB(pyodide);      // before Python: IDB callbacks still fire
        globalThis.syncSaves = makeSyncSaves(pyodide);

        self.postMessage({ type: 'status', msg: 'Installing Python packages…' });

        // jsonschema is a real runtime dependency: the save readers validate
        // against schemas/*.json on every load (see requirements.txt).
        await pyodide.loadPackage(['jsonschema']);

        self.postMessage({ type: 'status', msg: 'Downloading the village…' });

        const resp = await fetch('/web/game.zip');
        if (!resp.ok) throw new Error(`game.zip fetch failed: ${resp.status}`);
        const buf = await resp.arrayBuffer();
        pyodide.FS.mkdir('/game');
        pyodide.unpackArchive(new Uint8Array(buf), 'zip', { extractDir: '/game' });

        self.postMessage({ type: 'status', msg: 'Casting off…' });
        self.postMessage({ type: 'ready' });

        // chdir to /game so the cwd-relative schema paths in the save readers
        // resolve; FISHE_SAVE_DIR points Config at the IndexedDB-backed dir.
        await pyodide.runPythonAsync(`
import os, sys
sys.path.insert(0, '/game/src')
os.chdir('/game')
os.environ['FISHE_SAVE_DIR'] = '${SAVE_DIRECTORY}'
exec(open('/game/web/pyodide_main.py').read())
`);

    } catch (err) {
        self.postMessage({ type: 'error', msg: String(err) });
    }
};
