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
let lastPeriod = null;
let currentPredText = 'BIG 🔴';
let currentOutcome = 'WAITING…';
let winsCount = 0;

// Track history for the trend table
let history = [
    { periodNum: '---', pred: 'BIG 🔴', outcome: 'WAITING…' },
    { periodNum: '---', pred: 'SMALL 🟢', outcome: '✅' },
    { periodNum: '---', pred: 'SMALL 🟢', outcome: '❌' }
];

function getNextPeriod() {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    
    const currentHours = now.getUTCHours();
    const minutes = now.getUTCMinutes();
    const totalMinutes = (currentHours * 60) + minutes + 1; 
    const periodIndex = String(totalMinutes).padStart(4, '0');
    
    return `${dateStr}1M${periodIndex}`;
}

async function sendBroadcast(sock, period) {
    const shortCur = period ? period.slice(-3) : '---';
    const msg = `🤖 *FB999 1 MINUTE WINGO*\n\n` +
                `Period: ${period}\n` +
                `Prediction: *${currentPredText}*\n\n` +
                `Recent Trend:\n` +
                `PERIOD: ${shortCur}- ${currentPredText} ${currentOutcome}\n` +
                `PERIOD: ${history[0].periodNum}- ${history[0].pred} ${history[0].outcome}\n` +
                `PERIOD: ${history[1].periodNum}- ${history[1].pred} ${history[1].outcome}\n\n` +
                `Wins: ${winsCount}\n` +
                `Plan your stage\n\n` +
                `Status: Live & Synced`;

    for (const target of TARGETS) {
        try {
            await sock.sendMessage(target, { text: msg });
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
            await sock.sendMessage(ADMIN_JID, { text: '🛑 WinGo Signal Bot has been **STOPPED**.' });
        } else if (command === 'start') {
            isBotRunning = true;
            await sock.sendMessage(ADMIN_JID, { text: '✅ WinGo Signal Bot has been **STARTED**.' });
        } else if (command === 'win' || command === '✅') {
            if (currentOutcome === 'WAITING…') {
                currentOutcome = '✅';
                winsCount++;

                // Shift history forward when result is logged
                history[1] = { ...history[0] };
                history[0] = { periodNum: lastPeriod ? lastPeriod.slice(-3) : '---', pred: currentPredText, outcome: '✅' };

                // Automatically generate and drop the next period immediately upon result entry
                lastPeriod = getNextPeriod();
                const isBig = Math.random() < 0.5;
                currentPredText = isBig ? 'BIG 🔴' : 'SMALL 🟢';
                currentOutcome = 'WAITING…';

                await sock.sendMessage(ADMIN_JID, { text: `✅ Recorded WIN! New Period dropped.` });
                await sendBroadcast(sock, lastPeriod);
            }
        } else if (command === 'loss' || command === 'loose' || command === '❌') {
            if (currentOutcome === 'WAITING…') {
                currentOutcome = '❌';

                // Shift history forward when result is logged
                history[1] = { ...history[0] };
                history[0] = { periodNum: lastPeriod ? lastPeriod.slice(-3) : '---', pred: currentPredText, outcome: '❌' };

                // Automatically generate and drop the next period immediately upon result entry
                lastPeriod = getNextPeriod();
                const isBig = Math.random() < 0.5;
                currentPredText = isBig ? 'BIG 🔴' : 'SMALL 🟢';
                currentOutcome = 'WAITING…';

                await sock.sendMessage(ADMIN_JID, { text: `❌ Recorded LOSS! New Period dropped.` });
                await sendBroadcast(sock, lastPeriod);
            }
        }
    });

    // Initial first signal on startup if none exists
    setInterval(async () => {
        if (!isBotRunning || !sock || sock.user == null) return;
        if (!lastPeriod) {
            lastPeriod = getNextPeriod();
            const isBig = Math.random() < 0.5;
            currentPredText = isBig ? 'BIG 🔴' : 'SMALL 🟢';
            currentOutcome = 'WAITING…';
            await sendBroadcast(sock, lastPeriod);
        }
    }, 4000);
}

startBot();
