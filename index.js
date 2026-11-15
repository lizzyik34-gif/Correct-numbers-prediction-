const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const pino = require('pino');
const http = require('http');

// Render port requirement
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('WinGo Bot Active\n');
});
server.listen(process.env.PORT || 3000);

const ADMIN_NUMBER = '2349128299683';
const ADMIN_JID = `${ADMIN_NUMBER}@s.whatsapp.net`;
const TARGETS = [
    ADMIN_JID,                      // Private chat / Self chat
    '120363411622026272@g.us'        // Group chat
];

let isBotRunning = true;
let sockInstance = null;

// Independent states for each timeframe
let state30S = { lastPeriod: null, pred: 'BIG', outcome: '⏳', autoSkip: false, timer: null };
let state1M  = { lastPeriod: null, pred: 'SMALL', outcome: '⏳', autoSkip: false, timer: null };
let state3M  = { lastPeriod: null, pred: 'BIG', outcome: '⏳', autoSkip: false, timer: null };
let state5M  = { lastPeriod: null, pred: 'SMALL', outcome: '⏳', autoSkip: false, timer: null };

// Period generators
function getPeriod30S() {
    const now = new Date();
    const dateStr = `${now.getUTCFullYear()}${String(now.getUTCMonth() + 1).padStart(2, '0')}${String(now.getUTCDate()).padStart(2, '0')}`;
    const totalSeconds = (now.getUTCHours() * 3600) + (now.getUTCMinutes() * 60) + now.getUTCSeconds();
    return `${dateStr}30S${String(Math.floor(totalSeconds / 30) + 1).padStart(4, '0')}`;
}

function getPeriod1M() {
    const now = new Date();
    const dateStr = `${now.getUTCFullYear()}${String(now.getUTCMonth() + 1).padStart(2, '0')}${String(now.getUTCDate()).padStart(2, '0')}`;
    const totalMinutes = (now.getUTCHours() * 60) + now.getUTCMinutes() + 1;
    return `${dateStr}1M${String(totalMinutes).padStart(4, '0')}`;
}

function getPeriod3M() {
    const now = new Date();
    const dateStr = `${now.getUTCFullYear()}${String(now.getUTCMonth() + 1).padStart(2, '0')}${String(now.getUTCDate()).padStart(2, '0')}`;
    const totalMinutes = (now.getUTCHours() * 60) + now.getUTCMinutes();
    return `${dateStr}3M${String(Math.floor(totalMinutes / 3) + 1).padStart(4, '0')}`;
}

function getPeriod5M() {
    const now = new Date();
    const dateStr = `${now.getUTCFullYear()}${String(now.getUTCMonth() + 1).padStart(2, '0')}${String(now.getUTCDate()).padStart(2, '0')}`;
    const totalMinutes = (now.getUTCHours() * 60) + now.getUTCMinutes();
    return `${dateStr}5M${String(Math.floor(totalMinutes / 5) + 1).padStart(4, '0')}`;
}

async function sendSignal(title, period, pred, outcome) {
    if (!sockInstance || sockInstance.user == null) return;

    const msg = `🤖 *FB999 ${title} WINGO*\n\n` +
                `Period: ${period}\n` +
                `Prediction: *${pred}* ${outcome}\n\n` +
                `Status: Live & Synced`;

    for (const target of TARGETS) {
        try {
            await sockInstance.sendMessage(target, { text: msg });
        } catch (e) {
            console.log(`Failed to send to ${target}:`, e.message);
        }
    }
}

async function startBot() {
    console.log('Starting WhatsApp connection...');
    const { state, saveCreds } = await useMultiFileAuthState('auth_info');

    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        logger: pino({ level: 'silent' }),
        browser: ['Ubuntu', 'Chrome', '20.0.04']
    });

    sockInstance = sock;

    if (!sock.authState.creds.registered) {
        setTimeout(async () => {
            try {
                console.log('Requesting fresh pairing code...');
                const code = await sock.requestPairingCode(ADMIN_NUMBER);
                const formattedCode = code?.match(/.{1,4}/g)?.join('-') || code;
                console.log('\n====================================');
                console.log('👉 YOUR WHATSAPP PAIRING CODE:', formattedCode);
                console.log('⚠️ TYPE THIS CODE IN WHATSAPP WITHIN 30 SECONDS!');
                console.log('====================================\n');
            } catch (err) {
                console.log('Failed to get pairing code:', err.message);
            }
        }, 8000);
    }

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect } = update;
        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            console.log(`Connection closed (Status: ${statusCode}). Reconnecting...`);
            if (statusCode !== DisconnectReason.loggedOut) {
                setTimeout(startBot, 3000);
            }
        } else if (connection === 'open') {
            console.log('✅ Connected to WhatsApp successfully!');
        }
    });

    sock.ev.on('messages.upsert', async ({ messages }) => {
        const m = messages[0];
        if (!m.message || !m.key.remoteJid) return;

        const sender = m.key.remoteJid;
        const text = m.message.conversation || m.message.extendedTextMessage?.text;

        if (!text) return;

        const isFromAdmin = sender.includes(ADMIN_NUMBER) || m.key.fromMe;
        if (!isFromAdmin) return;

        const cmd = text.trim().toLowerCase();

        if (cmd === 'stop') {
            isBotRunning = false;
            [state30S, state1M, state3M, state5M].forEach(s => { if (s.timer) clearTimeout(s.timer); });
            await sock.sendMessage(ADMIN_JID, { text: '🛑 WinGo Signal Bot has been **STOPPED**.' });
            console.log('Bot stopped by admin command.');
        } else if (cmd === 'start') {
            isBotRunning = true;
            [state30S, state1M, state3M, state5M].forEach(s => s.autoSkip = false);
            await sock.sendMessage(ADMIN_JID, { text: '✅ WinGo Signal Bot has been **STARTED**.' });
            console.log('Bot started by admin command.');
        } 
        // 30 Seconds Control (e.g., "30s win", "30sec ✅", "30s loss")
        else if (cmd.includes('30')) {
            if (cmd.includes('win') || cmd.includes('✅')) {
                if (state30S.timer) clearTimeout(state30S.timer);
                state30S.outcome = '✅';
                state30S.autoSkip = false;
                await sock.sendMessage(ADMIN_JID, { text: `✅ Recorded 30S WIN!` });
            } else if (cmd.includes('loss') || cmd.includes('loose') || cmd.includes('❌')) {
                if (state30S.timer) clearTimeout(state30S.timer);
                state30S.outcome = '❌';
                state30S.autoSkip = true;
                await sock.sendMessage(ADMIN_JID, { text: `❌ Recorded 30S LOSS — Next 30S will SKIP!` });
            }
        }
        // 1 Minute Control (e.g., "1m win", "1min ✅", "1m loss")
        else if (cmd.includes('1m') || cmd.includes('1 min')) {
            if (cmd.includes('win') || cmd.includes('✅')) {
                if (state1M.timer) clearTimeout(state1M.timer);
                state1M.outcome = '✅';
                state1M.autoSkip = false;
                await sock.sendMessage(ADMIN_JID, { text: `✅ Recorded 1M WIN!` });
            } else if (cmd.includes('loss') || cmd.includes('loose') || cmd.includes('❌')) {
                if (state1M.timer) clearTimeout(state1M.timer);
                state1M.outcome = '❌';
                state1M.autoSkip = true;
                await sock.sendMessage(ADMIN_JID, { text: `❌ Recorded 1M LOSS — Next 1M will SKIP!` });
            }
        }
        // 3 Minutes Control (e.g., "3m win", "3min ✅", "3m loss")
        else if (cmd.includes('3m') || cmd.includes('3 min')) {
            if (cmd.includes('win') || cmd.includes('✅')) {
                if (state3M.timer) clearTimeout(state3M.timer);
                state3M.outcome = '✅';
                state3M.autoSkip = false;
                await sock.sendMessage(ADMIN_JID, { text: `✅ Recorded 3M WIN!` });
            } else if (cmd.includes('loss') || cmd.includes('loose') || cmd.includes('❌')) {
                if (state3M.timer) clearTimeout(state3M.timer);
                state3M.outcome = '❌';
                state3M.autoSkip = true;
                await sock.sendMessage(ADMIN_JID, { text: `❌ Recorded 3M LOSS — Next 3M will SKIP!` });
            }
        }
        // 5 Minutes Control (e.g., "5m win", "5min ✅", "5m loss")
        else if (cmd.includes('5m') || cmd.includes('5 min')) {
            if (cmd.includes('win') || cmd.includes('✅')) {
                if (state5M.timer) clearTimeout(state5M.timer);
                state5M.outcome = '✅';
                state5M.autoSkip = false;
                await sock.sendMessage(ADMIN_JID, { text: `✅ Recorded 5M WIN!` });
            } else if (cmd.includes('loss') || cmd.includes('loose') || cmd.includes('❌')) {
                if (state5M.timer) clearTimeout(state5M.timer);
                state5M.outcome = '❌';
                state5M.autoSkip = true;
                await sock.sendMessage(ADMIN_JID, { text: `❌ Recorded 5M LOSS — Next 5M will SKIP!` });
            }
        }
        // Default / Quick fallback if you just type "win" or "loss"
        else if (cmd === 'win' || cmd === '✅') {
            state1M.outcome = '✅';
            state1M.autoSkip = false;
            await sock.sendMessage(ADMIN_JID, { text: `✅ Recorded 1M WIN (Default)!` });
        } else if (cmd === 'loss' || cmd === 'loose' || cmd === '❌') {
            state1M.outcome = '❌';
            state1M.autoSkip = true;
            await sock.sendMessage(ADMIN_JID, { text: `❌ Recorded 1M LOSS (Default) — Next 1M will SKIP!` });
        }
    });

    // Independent background checkers for each timeframe
    setInterval(async () => {
        if (!isBotRunning || !sock || sock.user == null) return;

        // 30 SECONDS CHECK
        const p30 = getPeriod30S();
        if (p30 !== state30S.lastPeriod) {
            state30S.lastPeriod = p30;
            state30S.outcome = '⏳';
            if (state30S.autoSkip) {
                state30S.pred = 'SKIP ⏸';
                state30S.outcome = '⏸';
                state30S.autoSkip = false;
            } else {
                state30S.pred = Math.random() < 0.5 ? 'BIG' : 'SMALL';
                if (state30S.timer) clearTimeout(state30S.timer);
                state30S.timer = setTimeout(() => {
                    if (state30S.outcome === '⏳') {
                        state30S.outcome = '⏰';
                        state30S.autoSkip = true;
                    }
                }, 8000);
            }
            await sendSignal('30 SECONDS', p30, state30S.pred, state30S.outcome);
        }

        // 1 MINUTE CHECK
        const p1m = getPeriod1M();
        if (p1m !== state1M.lastPeriod) {
            state1M.lastPeriod = p1m;
            state1M.outcome = '⏳';
            if (state1M.autoSkip) {
                state1M.pred = 'SKIP ⏸';
                state1M.outcome = '⏸';
                state1M.autoSkip = false;
            } else {
                state1M.pred = Math.random() < 0.5 ? 'BIG' : 'SMALL';
                if (state1M.timer) clearTimeout(state1M.timer);
                state1M.timer = setTimeout(() => {
                    if (state1M.outcome === '⏳') {
                        state1M.outcome = '⏰';
                        state1M.autoSkip = true;
                    }
                }, 8000);
            }
            await sendSignal('1 MINUTE', p1m, state1M.pred, state1M.outcome);
        }

        // 3 MINUTES CHECK
        const p3m = getPeriod3M();
        if (p3m !== state3M.lastPeriod) {
            state3M.lastPeriod = p3m;
            state3M.outcome = '⏳';
            if (state3M.autoSkip) {
                state3M.pred = 'SKIP ⏸';
                state3M.outcome = '⏸';
                state3M.autoSkip = false;
            } else {
                state3M.pred = Math.random() < 0.5 ? 'BIG' : 'SMALL';
                if (state3M.timer) clearTimeout(state3M.timer);
                state3M.timer = setTimeout(() => {
                    if (state3M.outcome === '⏳') {
                        state3M.outcome = '⏰';
                        state3M.autoSkip = true;
                    }
                }, 8000);
            }
            await sendSignal('3 MINUTES', p3m, state3M.pred, state3M.outcome);
        }

        // 5 MINUTES CHECK
        const p5m = getPeriod5M();
        if (p5m !== state5M.lastPeriod) {
            state5M.lastPeriod = p5m;
            state5M.outcome = '⏳';
            if (state5M.autoSkip) {
                state5M.pred = 'SKIP ⏸';
                state5M.outcome = '⏸';
                state5M.autoSkip = false;
            } else {
                state5M.pred = Math.random() < 0.5 ? 'BIG' : 'SMALL';
                if (state5M.timer) clearTimeout(state5M.timer);
                state5M.timer = setTimeout(() => {
                    if (state5M.outcome === '⏳') {
                        state5M.outcome = '⏰';
                        state5M.autoSkip = true;
                    }
                }, 8000);
            }
            await sendSignal('5 MINUTES', p5m, state5M.pred, state5M.outcome);
        }
    }, 2000);
}

startBot();
