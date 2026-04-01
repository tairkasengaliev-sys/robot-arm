// relay.js - WebSocket Relay для роборуки
const WebSocket = require('ws');
const port = process.env.PORT || 8765;
const wss = new WebSocket.Server({ port });

let laptopClient = null;  // Ноутбук с Arduino
const webClients = new Set();  // Веб-клиенты

console.log(`🚀 Relay запущен на порту ${port}`);

wss.on('connection', (ws) => {
    console.log('🔌 Новое подключение');
    
    ws.on('message', (raw) => {
        let data;
        try { 
            data = JSON.parse(raw); 
        } catch { 
            console.log('⚠️ Неверный формат JSON');
            return; 
        }

        // Регистрация ноутбука с Arduino
        if (data.type === 'register' && data.role === 'arduino') {
            laptopClient = ws;
            console.log('✅ Ноутбук подключился');
            
            // Сообщить веб-клиентам
            webClients.forEach(c => {
                if (c.readyState === 1) {
                    c.send(JSON.stringify({ 
                        type: 'arduino_status', 
                        connected: true 
                    }));
                }
            });

        // Регистрация веб-клиента
        } else if (data.type === 'register' && data.role === 'web') {
            webClients.add(ws);
            console.log('🌐 Веб-клиент подключился');
            
            // Отправить текущий статус
            ws.send(JSON.stringify({ 
                type: 'arduino_status', 
                connected: !!(laptopClient && laptopClient.readyState === 1) 
            }));

        // Команда от веб-клиента
        } else if (data.type === 'command' || data.type === 'set') {
            if (laptopClient && laptopClient.readyState === 1) {
                laptopClient.send(raw.toString());
                console.log(`📤 Отправлено на Arduino: ${data.type}`);
            } else {
                ws.send(JSON.stringify({ 
                    type: 'error', 
                    message: 'Arduino не подключено' 
                }));
            }
        }
    });

    ws.on('close', () => {
        if (ws === laptopClient) {
            laptopClient = null;
            console.log('❌ Ноутбук отключился');
            
            // Сообщить веб-клиентам
            webClients.forEach(c => {
                if (c.readyState === 1) {
                    c.send(JSON.stringify({ 
                        type: 'arduino_status', 
                        connected: false 
                    }));
                }
            });
        }
        webClients.delete(ws);
        console.log('🔌 Клиент отключился');
    });
    
    ws.on('error', (err) => {
        console.log('⚠️ Ошибка WebSocket:', err.message);
    });
});

// Ping каждые 30 сек для keep-alive
setInterval(() => {
    wss.clients.forEach(ws => {
        if (ws.readyState === 1) {
            ws.ping();
        }
    });
}, 30000);
