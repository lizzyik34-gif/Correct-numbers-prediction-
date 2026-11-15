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

let lastPeriod30S = null;
let lastPeriod1M = null;
let lastPeriod3M = null;
let lastPeriod5M = null;

let currentPred30S = 'BIG';
let currentPred1M = 'SMALL';
let currentPred3M = 'BIG';
let currentPred5M = 'SMALL';

let currentOutcome30S = '⏳';
let currentOutcome1M = '⏳';
let currentOutcome3M = '⏳';
let currentOutcome5M = '⏳';

let autoSkip30S = false;
let autoSkip1M = false;
let autoSkip3M = false;
let autoSkip5M = false;

let timer30S = null;
let timer1M = null;

// Period generators for 30 Sec, 1 Min, 3 Min, and 5 Min
function getPeriod30S() {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    
    const totalSeconds = (now.getUTCHours() * 3600) + (now.getUTCMinutes() * 60) + now.getUTCSeconds();
    const periodIndex = Math.floor(totalSeconds / 30) + 1;
    return `${dateStr}30S${String(periodIndex).padStart(4, '0')}`;
}

function getPeriod1M() {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    
    const totalMinutes = (now.getUTCHours() * 60) + now.getUTCMinutes() + 1;
    return `${dateStr}1M${String(totalMinutes).padStart(4, '0')}`;
}

function getPeriod3M() {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    
    const totalMinutes = (now.getUTCHours() * 60) + now.getUTCMinutes();
    const periodIndex = Math.floor(totalMinutes / 3) + 1;
    return `${dateStr}3M${String(periodIndex).padStart(4, '0')}`;
}

function getPeriod5M() {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    
    const totalMinutes = (now.getUTCHours() * 60) + now.getUTCMinutes();
    const periodIndex = Math.floor(totalMinutes / 5) + 1;
    return `${dateStr}5M${String(periodIndex).padStart(4, '0')}`;
}

async function broadcastAllSignals() {
    if (!sockInstance || sockInstance.user == null) return;

    const msg = `🤖 *FB999 MULTI-TIMEFRAME WINGO*\n\n` +
                `⏱ *30 SECONDS*\n` +
                `Period: ${lastPeriod30S || '---'}\n` +
                `Prediction: *${currentPred30S}* ${currentOutcome30S}\n\n` +
                `⏱ *1 MINUTE*\n` +
                `Period: ${lastPeriod1M || '---'}\n` +
                `Prediction: *${currentPred1M}* ${currentOutcome1M}\n\n` +
                `⏱ *3 MINUTES*\n` +
                `Period: ${lastPeriod3M || '---'}\n` +
                `Prediction: *${currentPred3M}* ${currentOutcome3M}\n\n` +
                `⏱ *5 MINUTES*\n` +
                `Period: ${lastPeriod5M || '---'}\n` +
                `Prediction: *${currentPred5M}* ${currentOutcome5M}\n\n` +
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

        const command = text.trim().toLowerCase();

        if (command === 'stop') {
            isBotRunning = false;
            if (timer30S) clearTimeout(timer30S);
            if (timer1M) clearTimeout(timer1M);
            await sock.sendMessage(ADMIN_JID, { text: '🛑 WinGo Signal Bot has been **STOPPED**.' });
            console.log('Bot stopped by admin command.');
        } else if (command === 'start') {
            isBotRunning = true;
            autoSkip30S = false;
            autoSkip1M = false;
            autoSkip3M = false;
            autoSkip5M = false;
            await sock.sendMessage(ADMIN_JID, { text: '✅ WinGo Signal Bot has been **STARTED**.' });
            console.log('Bot started by admin command.');
        } else if (command === 'win' || command === '✅') {
            if (timer30S) clearTimeout(timer30S);
            if (timer1M) clearTimeout(timer1M);
            currentOutcome30S = '✅';
            currentOutcome1M = '✅';
            autoSkip30S = false;
            autoSkip1M = false;
            await broadcastAllSignals();
            await sock.sendMessage(ADMIN_JID, { text: `✅ Recorded WIN on live signals!` });
        } else if (command === 'loss' || command === 'loose' || command === '❌') {
            if (timer30S) clearTimeout(timer30S);
            if (timer1M) clearTimeout(timer1M);
            currentOutcome30S = '❌';
            currentOutcome1M = '❌';
            autoSkip30S = true;
            autoSkip1M = true; // Auto-skip next periods on loss
            await broadcastAllSignals();
            await sock.sendMessage(ADMIN_JID, { text: `❌ Recorded LOSS — Next periods will SKIP!` });
        }
    });

    // Main check loop running every 2 seconds to catch period shifts smoothly across all 4 timers
    setInterval(async () => {
        if (!isBotRunning || !sock || sock.user == null) return;

        let updated = false;

        // Check 30 Sec Timer
        const p30 = getPeriod30S();
        if (p30 !== lastPeriod30S) {
            lastPeriod30S = p30;
            currentOutcome30S = '⏳';
            if (autoSkip30S) {
                currentPred30S = 'SKIP ⏸';
                currentOutcome30S = '⏸';
                autoSkip30S = false;
            } else {
                currentPred30S = Math.random() < 0.5 ? 'BIG' : 'SMALL';
                if (timer30S) clearTimeout(timer30S);
                timer30S = setTimeout(() => {
                    if (currentOutcome30S === '⏳') {
                        currentOutcome30S = '⏰';
                        autoSkip30S = true;
                        broadcastAllSignals();
                    }
                }, 8000);
            }
            updated = true;
        }

        // Check 1 Min Timer
        const p1m = getPeriod1M();
        if (p1m !== lastPeriod1M) {
            lastPeriod1M = p1m;
            currentOutcome1M = '⏳';
            if (autoSkip1M) {
                currentPred1M = 'SKIP ⏸';
                currentOutcome1M = '⏸';
                autoSkip1M = false;
            } else {
                currentPred1M = Math.random() < 0.5 ? 'BIG' : 'SMALL';
                if (timer1M) clearTimeout(timer1M);
                timer1M = setTimeout(() => {
                    if (currentOutcome1M === '⏳') {
                        currentOutcome1M = '⏰';
                        autoSkip1M = true;
                        broadcastAllSignals();
                    }
                }, 8000);
            }
            updated = true;
        }

        // Check 3 Min Timer
        const p3m = getPeriod3M();
        if (p3m !== lastPeriod3M) {
            lastPeriod3M = p3m;
            currentOutcome3M = '⏳';
            currentPred3M = Math.random() < 0.5 ? 'BIG' : 'SMALL';
            updated = true;
        }

        // Check 5 Min Timer
        const p5m = getPeriod5M();
        if (p5m !== lastPeriod5M) {
            lastPeriod5M = p5m;
            currentOutcome5M = '⏳';
            currentPred5M = Math.random() < 0.5 ? 'BIG' : 'SMALL';
            updated = true;
        }

        if (updated) {
            await broadcastAllSignals();
        }
    }, 2000);
}

startBot();
